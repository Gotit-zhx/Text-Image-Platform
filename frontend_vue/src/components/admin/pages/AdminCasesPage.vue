<script setup lang="ts">
import {onBeforeUnmount,ref,watch} from 'vue'
import DOMPurify from 'dompurify'
import {apiRequest} from '../../../api/client'
import type {Paged} from '../../../api/community'
const props=defineProps<{kind:'reports'|'appeals';canModerate:boolean;canOperate:boolean}>()
type CaseRecord={id:number;status:string;targetType?:string;targetId?:number;postId?:number;reason?:string;description:string;context:Record<string,unknown>;outcome:string;createdAt:string}
const items=ref<CaseRecord[]>([]),page=ref(1),total=ref(0),status=ref('open'),pending=ref(false),error=ref(''),selected=ref<CaseRecord>(),action=ref('dismiss'),reason=ref('')
let version=0,controller:AbortController|undefined
const load=async()=>{
  const current=++version,kind=props.kind
  controller?.abort();controller=new AbortController()
  pending.value=true;error.value=''
  try{
    const result=await apiRequest<Paged<CaseRecord>>(`/admin/${kind}?page=${page.value}&status=${status.value}`,{signal:controller.signal})
    if(current!==version)return
    items.value=result.items;total.value=result.pagination.total
  }catch(e){
    if(current===version&&!(e instanceof Error&&e.name==='AbortError'))error.value=e instanceof Error?e.message:'加载失败'
  }finally{if(current===version)pending.value=false}
}
const decide=async()=>{
  if(!selected.value||pending.value)return
  const current=version,kind=props.kind,targetId=selected.value.id
  pending.value=true;error.value=''
  try{
    await apiRequest(`/admin/${kind}/${targetId}/resolve`,{method:'POST',body:JSON.stringify({action:action.value,reason:reason.value})})
    if(current!==version)return
    selected.value=undefined;reason.value='';await load()
  }catch(e){if(current===version)error.value=e instanceof Error?e.message:'处理失败'}
  finally{if(current===version)pending.value=false}
}
watch(()=>props.kind,()=>{
  page.value=1;status.value='open';items.value=[];total.value=0
  selected.value=undefined;reason.value='';action.value='dismiss'
  void load()
},{immediate:true})
onBeforeUnmount(()=>{version++;controller?.abort()})
</script>
<template>
  <el-card shadow="never" class="case-panel">
    <header class="head">
      <h2>{{ kind === 'reports' ? '举报受理' : '申诉复核' }}</h2>
      <div class="filters">
    <el-select v-model="status" :aria-label="kind === 'reports' ? '举报状态' : '申诉状态'" style="width:160px" @change="page=1;load()">
      <el-option label="待处理" value="open" />
      <el-option label="已处置" value="resolved" />
      <el-option label="不予处置" value="dismissed" />
      <el-option label="全部" value="" />
    </el-select>
    <el-button @click="load">刷新</el-button>
      </div>
    </header>
    <el-alert v-if="error" :title="error" type="error" :closable="false" />
    <el-table v-loading="pending" :data="items" :aria-busy="pending">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="reason" label="举报原因" min-width="140" />
      <el-table-column prop="description" label="说明" min-width="180" />
      <el-table-column label="状态" width="100">
        <template #default="scope">{{ ({open:'待处理',resolved:'已处置',dismissed:'不予处置'} as Record<string,string>)[scope.row.status] || scope.row.status }}</template>
      </el-table-column>
      <el-table-column prop="outcome" label="结果" min-width="160" />
      <el-table-column label="上下文 / 处理" width="150">
        <template #default="scope">
          <el-button :disabled="pending" @click="selected=scope.row;action='dismiss';reason='';error=''">查看记录</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination class="pager" layout="total,prev,pager,next" :background="true" :total="total" :page-size="20" :current-page="page" @current-change="(value:number)=>{page=value;load()}" />
    <el-dialog :model-value="!!selected" title="上下文与处置" width="min(700px,94vw)" @close="selected=undefined">
      <template v-if="selected">
        <p>{{ selected.reason }} {{ selected.description }}</p>
        <section class="context-card">
          <h3>{{ kind === 'reports' ? '被举报内容' : '申诉作品' }}</h3>
          <p v-if="selected.context.title">标题：{{ selected.context.title }}</p>
          <p v-if="selected.context.summary">摘要：{{ selected.context.summary }}</p>
          <div v-if="selected.context.contentHtml" class="case-content" v-html="DOMPurify.sanitize(String(selected.context.contentHtml))" />
          <p v-if="selected.context.content">评论：{{ selected.context.content }}</p>
          <p v-if="selected.context.name">用户：{{ selected.context.name }}</p>
          <p v-if="selected.context.status">状态：{{ ({approved:'已公开',pending:'待审核',offline:'已下架',rejected:'已驳回'} as Record<string,string>)[String(selected.context.status)] || selected.context.status }}</p>
          <p v-if="selected.context.unavailable || selected.context.deleted">目标已不可用。</p>
          <RouterLink v-if="!selected.context.deleted && !selected.context.unavailable" to="/admin/posts" class="text-button">查看审核队列</RouterLink>
        </section>
        <p v-if="selected.outcome">结果：{{ selected.outcome }}</p>
        <form v-if="selected.status === 'open' && ((selected.targetType === 'user' && canOperate) || (selected.targetType !== 'user' && canModerate))" @submit.prevent="decide">
          <label>处理动作
            <el-select v-model="action" aria-label="处理动作" :disabled="pending">
              <el-option label="不予处置" value="dismiss" />
              <el-option v-if="kind === 'appeals'" label="申诉通过，恢复公开" value="approve" />
              <el-option v-if="kind === 'reports' && selected.targetType === 'post'" label="下架作品" value="offline" />
              <el-option v-if="kind === 'reports' && selected.targetType === 'comment'" label="隐藏评论" value="hide" />
              <template v-if="kind === 'reports' && selected.targetType === 'user'">
                <el-option label="禁言7天" value="mute" />
                <el-option label="封禁" value="ban" />
              </template>
            </el-select>
          </label>
          <label>处理理由
            <el-input v-model="reason" aria-label="处理理由" type="textarea" :readonly="pending" maxlength="500" placeholder="必须填写处理依据" />
          </label>
          <el-alert v-if="error" :title="error" type="error" />
          <el-button native-type="submit" type="primary" :loading="pending" :disabled="!reason.trim()">确认处理</el-button>
        </form>
        <p v-else-if="selected.status === 'open'">当前角色仅可查看。</p>
      </template>
    </el-dialog>
  </el-card>
</template>
<style scoped>
.case-panel :deep(.el-card__body) { padding: 16px; }
.head { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 12px; }
.head h2 { margin: 0; font-size: 16px; font-weight: 700; }
.filters { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.pager { justify-content: flex-end; flex-wrap: wrap; white-space: normal; margin-top: 12px; }
.case-content { max-height: 320px; overflow: auto; border: 1px solid var(--border); border-radius: var(--radius-control); padding: 16px; }
.case-content :deep(img) { max-width: 100%; height: auto; }
label { display: block; margin: 16px 0; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; background: var(--bg); padding: 16px; }
</style>
