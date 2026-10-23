// Real UI inspection only. No moderation, role changes, or account restrictions are submitted.
export async function runGovernanceContextAcceptance(tab, {origin,outputDir,fs}) {
  const checks=[]
  const assert=(condition,message)=>{if(!condition)throw new Error(message);checks.push(message)}
  const all=async(label)=>{
    await tab.playwright.getByRole('combobox',{name:label,exact:true}).click()
    await tab.playwright.getByRole('option',{name:'全部',exact:true}).click()
    await tab.playwright.locator('[aria-busy="true"]').waitFor({state:'hidden'})
    await tab.playwright.locator('.el-loading-mask').waitFor({state:'hidden'})
  }
  await tab.goto(origin+'/admin/reports')
  await tab.playwright.getByRole('heading',{name:'举报受理',exact:true}).waitFor({state:'visible'})
  await all('举报状态')
  assert(await tab.playwright.getByRole('button',{name:'查看记录',exact:true}).count()>0,'真实举报记录可读取')
  await tab.playwright.getByRole('menuitem',{name:'申诉复核',exact:true}).click()
  await tab.playwright.getByRole('heading',{name:'申诉复核',exact:true}).waitFor({state:'visible'})
  await tab.back()
  await tab.playwright.getByRole('heading',{name:'举报受理',exact:true}).waitFor({state:'visible'})
  await all('举报状态')
  await tab.playwright.getByRole('button',{name:'查看记录',exact:true}).first().click()
  await tab.playwright.getByRole('dialog',{name:'上下文与处置',exact:true}).waitFor({state:'visible'})
  assert(await tab.playwright.getByRole('heading',{name:'被举报内容',exact:true}).isVisible(),'举报弹层显示举报上下文')
  await tab.forward()
  await tab.playwright.getByRole('heading',{name:'申诉复核',exact:true}).waitFor({state:'visible'})
  await tab.playwright.getByRole('dialog',{name:'上下文与处置',exact:true}).waitFor({state:'hidden'})
  assert(await tab.playwright.getByRole('dialog',{name:'上下文与处置',exact:true}).count()===0,'浏览器前进不保留上一类处置目标')
  await all('申诉状态')
  await tab.playwright.getByRole('button',{name:'查看记录',exact:true}).first().click()
  await tab.playwright.getByRole('heading',{name:'申诉作品',exact:true}).waitFor({state:'visible'})
  assert(await tab.playwright.getByRole('heading',{name:'被举报内容',exact:true}).count()===0,'申诉弹层使用当前申诉上下文')
  await fs.mkdir(outputDir,{recursive:true})
  await fs.writeFile(outputDir+'/admin-context-replay.jpg',await tab.screenshot({fullPage:false}))
  await fs.writeFile(outputDir+'/admin-context-results.json',JSON.stringify({checks,passed:checks.length,date:'2026-10-22'},null,2))
  await tab.playwright.getByRole('button',{name:'Close this dialog',exact:true}).click()
  await tab.playwright.getByRole('dialog',{name:'上下文与处置',exact:true}).waitFor({state:'hidden'})
  return checks
}

export async function runAdminSearchRaceAcceptance(tab,{origin,controlPath,outputDir,fs}) {
  const checks=[]
  const assert=(condition,message)=>{if(!condition)throw new Error(message);checks.push(message)}
  await tab.goto(origin+'/admin/users')
  const input=tab.playwright.getByRole('textbox',{name:'用户关键词',exact:true})
  await input.waitFor({state:'visible'})
  await tab.playwright.locator('[aria-busy="true"]').waitFor({state:'hidden'})
  await fs.writeFile(controlPath,JSON.stringify({rules:[{method:'GET',path:'/api/admin/users',mode:'delay_after',delay_ms:2500,remaining:1}]}))
  await input.fill('acceptance_a')
  await tab.playwright.getByRole('button',{name:'查询',exact:true}).click()
  await input.fill('no-match-admin-race')
  await tab.playwright.getByRole('button',{name:'查询',exact:true}).click()
  await tab.playwright.locator('[aria-busy="true"]').waitFor({state:'hidden'})
  assert(await tab.playwright.locator('.el-table__body tr').count()===0,'延迟旧查询不覆盖最新无结果条件')
  assert(await input.evaluate(element=>element.value)==='no-match-admin-race','保留最新管理查询输入')
  assert(!(await tab.playwright.locator('main').innerText()).includes('已有请求正在处理'),'新查询不被其他读取全局锁拒绝')
  await fs.mkdir(outputDir,{recursive:true})
  await fs.writeFile(outputDir+'/admin-search-race.jpg',await tab.screenshot({fullPage:false}))
  await fs.writeFile(outputDir+'/admin-search-race-results.json',JSON.stringify({checks,passed:checks.length,date:'2026-10-22'},null,2))
  return checks
}
