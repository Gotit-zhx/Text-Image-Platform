// Run against the loopback fault_proxy.py and an explicitly isolated database.
// fs only controls the local proxy. Every product action uses the real browser UI.
export async function runCommentFailureAcceptance(tab, {origin, outputDir, controlPath, fs, postId, text}) {
  const checks=[]
  const assert=(value,message)=>{if(!value)throw new Error(message);checks.push(message)}
  const arm=async(mode)=>{
    const temp=controlPath+'.next'
    await fs.writeFile(temp,JSON.stringify({rules:[{
      method:'POST',path:`/api/community/posts/${postId}/comments`,mode,remaining:1,delay_ms:17000
    }]}))
    await fs.rename(temp,controlPath)
  }
  const visible=async(locator)=>{
    const until=Date.now()+24000
    while(true){
      try{await locator.waitFor({state:'visible',timeoutMs:3000});return}
      catch(error){if(Date.now()>=until)throw error}
    }
  }
  await tab.goto(`${origin}/detail/${postId}`)
  const input=tab.playwright.getByRole('textbox',{name:'写评论',exact:true})
  const send=tab.playwright.getByRole('button',{name:'发送评论',exact:true})
  await input.fill(text)
  for(const [mode,errorText,label] of [
    ['error','验收模拟服务错误','500'],
    ['disconnect','请求失败（500）','上游断连'],
    ['hold','请求超时','写入前超时'],
    ['delay_after','请求超时','提交后响应超时']
  ]){
    await arm(mode)
    await send.click()
    await visible(tab.playwright.getByRole('alert').filter({hasText:errorText}))
    assert(await input.evaluate(e=>e.value)===text,`${label}保留未确认输入`)
    assert((await tab.url()).includes(`/detail/${postId}`),`${label}保持原页面`)
  }
  await send.click()
  const comment=tab.playwright.locator('.comment').filter({hasText:text})
  await visible(comment)
  assert(await comment.count()===1,'手动重试只显示一条评论')
  assert(await input.evaluate(e=>e.value)==='','服务器确认后清空输入')
  await fs.mkdir(outputDir,{recursive:true})
  await fs.writeFile(outputDir+'/comment-failure-e2e.jpg',await tab.screenshot({fullPage:false}))
  await fs.writeFile(outputDir+'/comment-failure-e2e.json',JSON.stringify({date:'2026-10-22',postId,text,checks,passed:checks.length},null,2))
  return checks
}
