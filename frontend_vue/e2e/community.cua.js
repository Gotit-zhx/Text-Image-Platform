// Replay with the Codex browser runtime. Uses the real local UI and current session.
// Call: await runCommunityAcceptance(tab, { origin, outputDir, fs })
// The supplied fs is node:fs/promises from the CUA REPL; no browser/network bypass.
// Regression: the initial '/' route can resolve without changing fullPath.
export async function runInitialDetailAcceptance(tab, { origin }) {
  const checks = []
  await tab.goto(origin + '/')
  await tab.reload()
  await tab.playwright.locator('.post-card .content-link').first().waitFor({ state: 'visible' })
  await tab.getAXState()
  const count = await tab.playwright.locator('.post-card').count()
  const link = tab.playwright.locator('.post-card .content-link').first()
  const href = await link.getAttribute('href')
  await link.click()
  await tab.getAXState()
  await tab.playwright.getByRole('heading', { name: '作品详情', exact: true }).waitFor({ state: 'visible' })
  if (!(await tab.url()).endsWith(href)) throw new Error('详情 URL 未更新')
  checks.push('刷新首页后首次点击打开背景详情弹层')
  await tab.playwright.getByRole('button', { name: 'Close this dialog', exact: true }).click()
  await tab.getAXState()
  if (await tab.playwright.locator('.post-card').count() !== count) throw new Error('关闭详情丢失列表')
  checks.push('关闭详情保留首页列表')
  await tab.forward()
  await tab.getAXState()
  await tab.playwright.getByRole('heading', { name: '作品详情', exact: true }).waitFor({ state: 'visible' })
  checks.push('浏览器前进恢复详情弹层')
  await tab.reload()
  await tab.getAXState()
  await tab.playwright.getByRole('button', { name: '返回', exact: true }).waitFor({ state: 'visible' })
  if (await tab.playwright.getByRole('heading', { name: '作品详情', exact: true }).count()) {
    throw new Error('刷新详情错误复用了背景')
  }
  checks.push('详情刷新使用完整页面')
  return checks
}

export async function runCommunityAcceptance(tab, { origin, outputDir, fs }) {
  const checks = []
  const assert = (condition, message) => {
    if (!condition) throw new Error(message)
    checks.push(message)
  }
  await tab.goto(origin + '/?nav=更新')
  await tab.playwright
    .getByRole('heading', { name: '发现', exact: true })
    .waitFor({ state: 'visible' })
  await tab.playwright
    .getByRole('button', { name: '加载更多', exact: true })
    .waitFor({ state: 'visible' })
  const firstCount = await tab.playwright.locator('.post-card').count()
  await tab.playwright.getByRole('button', { name: '加载更多', exact: true }).click()
  await tab.playwright.locator('.post-card').nth(firstCount).waitFor({ state: 'visible' })
  const count = await tab.playwright.locator('.post-card').count()
  assert(count > firstCount, '真实分页追加内容')
  const hrefs = await tab.playwright
    .locator('.post-card .content-link')
    .evaluateAll((links) => links.map((link) => link.getAttribute('href')))
  assert(new Set(hrefs).size === hrefs.length, '分页按稳定ID去重')
  const link = tab.playwright.locator('.post-card .content-link').first()
  const href = await link.getAttribute('href')
  await link.click()
  await tab.playwright
    .getByRole('heading', { name: '作品详情', exact: true })
    .waitFor({ state: 'visible' })
  assert((await tab.url()).endsWith(href), '列表进入详情更新独立URL')
  await tab.playwright.getByRole('button', { name: 'Close this dialog', exact: true }).click()
  await tab.playwright
    .getByRole('heading', { name: '发现', exact: true })
    .waitFor({ state: 'visible' })
  assert((await tab.playwright.locator('.post-card').count()) === count, '关闭弹层保留已加载分页')
  await tab.forward()
  await tab.playwright
    .getByRole('heading', { name: '作品详情', exact: true })
    .waitFor({ state: 'visible' })
  assert((await tab.url()).endsWith(href), '前进重新打开详情')
  await tab.reload()
  await tab.playwright
    .getByRole('button', { name: '返回', exact: true })
    .waitFor({ state: 'visible' })
  await tab.playwright
    .getByRole('heading', { name: '评论与讨论', exact: true })
    .waitFor({ state: 'visible' })
  assert(
    (await tab.playwright.getByRole('heading', { name: '作品详情', exact: true }).count()) === 0,
    '详情刷新使用完整页面'
  )
  await tab.goto(origin + '/search?q=验收用户A&type=users')
  await tab.playwright
    .getByRole('link', { name: '验收用户A', exact: true })
    .waitFor({ state: 'visible' })
  assert((await tab.url()).includes('type=users'), '搜索URL可恢复且返回真实用户')
  await tab.playwright.getByRole('link', { name: '验收用户A', exact: true }).click()
  await tab.playwright
    .getByRole('heading', { name: '验收用户A', exact: true })
    .waitFor({ state: 'visible' })
  assert((await tab.url()).includes('/u/'), '用户主页使用稳定ID')
  await fs.mkdir(outputDir, { recursive: true })
  await fs.writeFile(
    outputDir + '/browser-e2e-profile.jpg',
    await tab.screenshot({ fullPage: false })
  )
  await fs.writeFile(
    outputDir + '/browser-e2e-results.json',
    JSON.stringify({ checks, passed: checks.length, date: '2026-10-22' }, null, 2)
  )
  return checks
}

// Keyboard-only controls and discussion pagination against explicit acceptance fixtures.
// No password changes, account deletion, or irreversible content deletion are performed.
export async function runInteractionAcceptance(tab, {origin, outputDir, fs, imagePostId=26, discussionPostId=25}) {
  const checks=[]
  const assert=(condition,message)=>{if(!condition)throw new Error(message);checks.push(message)}
  const focusState=()=>tab.playwright.evaluate(()=>{
    const focused=document.activeElement
    const dialog=focused?.closest('[role="dialog"]')
    return {tag:focused?.tagName,label:focused?.getAttribute('aria-label'),dialog:dialog?.getAttribute('aria-label')||dialog?.querySelector('h2')?.textContent,href:focused?.getAttribute('href'),locked:document.body.classList.contains('el-popup-parent--hidden')}
  })
  await tab.goto(origin+'/?nav=更新')
  const first=tab.playwright.locator(`.post-card .content-link[href="/detail/${imagePostId}"]`)
  await first.waitFor({state:'visible'})
  const href=await first.getAttribute('href')
  await first.press('Enter')
  const close=tab.playwright.getByRole('button',{name:'Close this dialog',exact:true})
  await close.waitFor({state:'visible'})
  assert((await tab.url()).endsWith(href),'键盘Enter打开详情URL')
  for(let i=0;i<12;i++){
    const current=await focusState()
    assert(Boolean(current.dialog),'详情Tab焦点始终在弹层内 '+(i+1))
    await tab.playwright.locator(':focus').press('Tab')
  }
  assert((await focusState()).locked,'详情背景滚动已锁定')
  const image=tab.playwright.getByRole('button',{name:'查看第1张图片',exact:true})
  await image.press('Enter')
  const group=tab.playwright.getByRole('group',{name:'图片查看区域，左右键切图，加减键缩放',exact:true})
  await group.waitFor({state:'visible'})
  await tab.playwright.locator('.viewer:focus').waitFor({state:'visible'})
  assert((await focusState()).label==='图片查看区域，左右键切图，加减键缩放','图片查看器打开即获得键盘焦点')
  await group.press('ArrowRight')
  assert((await group.innerText()).includes('2 / 2'),'方向键切换下一张图片')
  await group.press('+')
  assert((await group.innerText()).includes('150%'),'加号键缩放图片')
  await group.press('-')
  assert((await group.innerText()).includes('100%'),'减号键恢复缩放')
  for(let i=0;i<9;i++){
    assert((await focusState()).dialog==='图片查看器','嵌套查看器Tab焦点约束 '+(i+1))
    await tab.playwright.locator(':focus').press('Tab')
  }
  await tab.playwright.locator(':focus').press('Escape')
  await group.waitFor({state:'hidden'})
  assert(await image.isVisible(),'Esc先关闭图片查看器并保留详情')
  assert((await focusState()).label==='查看第1张图片','图片关闭后返回触发图片焦点')
  await tab.playwright.locator(':focus').press('Escape')
  await tab.playwright.getByRole('heading',{name:'发现',exact:true}).waitFor({state:'visible'})
  assert((await focusState()).href===href,'详情Esc关闭返回触发卡片焦点')
  await tab.playwright.locator('body.el-popup-parent--hidden').waitFor({state:'hidden'})
  assert(!(await focusState()).locked,'所有弹层关闭后解锁背景滚动')
  await tab.goto(origin+'/detail/'+discussionPostId)
  const input=tab.playwright.getByRole('textbox',{name:'写评论',exact:true})
  await input.waitFor({state:'visible'})
  const draft='键盘与排序验收：输入在热门和最新切换时保留'
  await input.fill(draft)
  await tab.playwright.getByRole('combobox',{name:'排序',exact:true}).selectOption('hot')
  await tab.playwright.locator('.skeleton').first().waitFor({state:'hidden'})
  assert(await input.evaluate(element=>element.value)===draft,'切换热门排序保留未发送输入')
  await tab.playwright.getByRole('combobox',{name:'排序',exact:true}).selectOption('latest')
  await tab.playwright.locator('.skeleton').first().waitFor({state:'hidden'})
  assert(await input.evaluate(element=>element.value)===draft,'切换最新排序保留未发送输入')
  for(let i=0;i<4&&await tab.playwright.getByRole('button',{name:'加载更多评论',exact:true}).count();i++){
    const count=await tab.playwright.locator('.comment:not(.child)').count()
    await tab.playwright.getByRole('button',{name:'加载更多评论',exact:true}).click()
    await tab.playwright.locator('.comment:not(.child)').nth(count).waitFor({state:'visible'})
  }
  assert(await tab.playwright.locator('.comment:not(.child)').count()===61,'浏览器完整读取61条根评论')
  await tab.playwright.getByRole('button',{name:'展开更多回复（31）',exact:true}).click()
  await tab.playwright.locator('.comment.child').nth(19).waitFor({state:'visible'})
  await tab.playwright.getByRole('button',{name:'展开更多回复（31）',exact:true}).click()
  await tab.playwright.locator('.comment.child').nth(30).waitFor({state:'visible'})
  assert(await tab.playwright.locator('.comment.child').count()===31,'浏览器完整读取31条楼中楼回复')
  const reply=tab.playwright.locator('.comment.child').first().getByRole('button',{name:'回复',exact:true})
  await reply.press('Enter')
  assert((await input.evaluate(element=>element===document.activeElement)),'键盘回复使评论输入获得焦点')
  assert(await tab.playwright.getByRole('button',{name:'取消回复',exact:true}).isVisible(),'楼中楼显示明确回复对象并可取消')
  await tab.playwright.getByRole('button',{name:'取消回复',exact:true}).click()
  assert(await input.evaluate(element=>element.value)===draft,'取消回复保留已输入文本')
  await input.fill('')
  await fs.mkdir(outputDir,{recursive:true})
  await fs.writeFile(outputDir+'/interaction-keyboard-pagination.jpg',await tab.screenshot({fullPage:false}))
  await fs.writeFile(outputDir+'/interaction-e2e-results.json',JSON.stringify({checks,passed:checks.length,date:'2026-10-22'},null,2))
  return checks
}

// Isolated server fixture hook expires only the supplied test account's sessions.
// Existing test credentials are entered through the UI; this never changes credentials.
export async function runEditRecoveryAcceptance(tab, {origin, postId, account, password, expireSession, outputDir, fs}) {
  const checks = []
  const assert = (condition, message) => {
    if (!condition) throw new Error(message)
    checks.push(message)
  }
  await tab.goto(`${origin}/edit/${postId}`)
  await tab.playwright.getByRole('heading', {name:'编辑作品',exact:true}).waitFor({state:'visible'})
  const title = tab.playwright.getByRole('textbox', {name:'标题',exact:true})
  const body = tab.playwright.getByRole('textbox', {name:'正文',exact:true})
  const expectedTitle = `编辑过期验收：${Date.now()}`
  const expectedBody = '这段未提交的文字需要在会话失效和同账号重新登录后保持完整。'
  await title.fill(expectedTitle)
  await body.press('ControlOrMeta+A')
  await body.pressSequentially(expectedBody)
  await expireSession()
  await tab.playwright.getByRole('button', {name:'确认保存',exact:true}).click()
  const login = tab.playwright.getByRole('dialog', {name:'密码登录',exact:true})
  await login.waitFor({state:'visible'})
  assert(await title.evaluate(element=>element.value) === expectedTitle, '编辑401保留标题')
  assert(await body.textContent() === expectedBody, '编辑401保留富文本正文')
  await login.getByRole('textbox', {name:'用户名或邮箱',exact:true}).fill(account)
  await login.getByRole('textbox', {name:'密码',exact:true}).fill(password)
  await login.getByRole('button', {name:'登录',exact:true}).click()
  await login.waitFor({state:'hidden'})
  assert(await title.evaluate(element=>element.value) === expectedTitle, '同账号重新登录保留编辑标题')
  assert(await body.textContent() === expectedBody, '同账号重新登录保留编辑正文')
  assert((await tab.url()).includes(`/edit/${postId}`), '登录后不静默保存或跳转')
  await tab.playwright.getByRole('button', {name:'确认保存',exact:true}).click()
  await tab.playwright.getByRole('heading', {name:expectedTitle,exact:true}).waitFor({state:'visible'})
  assert((await tab.url()).endsWith(`/detail/${postId}`), '用户显式重试保存后进入原作品详情')
  assert((await tab.playwright.locator('.prose').textContent()) === expectedBody, '重新读取的作品正文完整')
  await fs.mkdir(outputDir, {recursive:true})
  await fs.writeFile(outputDir+'/edit-session-replay.jpg', await tab.screenshot({fullPage:false}))
  await fs.writeFile(outputDir+'/edit-session-results.json', JSON.stringify({checks,passed:checks.length,date:'2026-10-22'},null,2))
  return checks
}

export async function runCommentSessionAcceptance(tab, {origin, postId, account, password, expireSession, outputDir, fs}) {
  const checks = []
  const assert = (condition, message) => {
    if (!condition) throw new Error(message)
    checks.push(message)
  }
  await tab.goto(`${origin}/detail/${postId}`)
  const input = tab.playwright.getByRole('textbox', {name:'写评论',exact:true})
  const text = `评论会话恢复验收 ${Date.now()}`
  await input.fill(text)
  await expireSession()
  await tab.playwright.getByRole('button', {name:'发送评论',exact:true}).click()
  const login = tab.playwright.getByRole('dialog', {name:'密码登录',exact:true})
  await login.waitFor({state:'visible'})
  assert(await input.evaluate(element=>element.value) === text, '详情会话过期后保留未发送评论')
  await login.getByRole('textbox', {name:'用户名或邮箱',exact:true}).fill(account)
  await login.getByRole('textbox', {name:'密码',exact:true}).fill(password)
  await login.getByRole('button', {name:'登录',exact:true}).click()
  await login.waitFor({state:'hidden'})
  assert(await input.evaluate(element=>element.value) === text, '同账号重登后保留评论正文')
  const comment = tab.playwright.locator('.comment').filter({hasText:text})
  assert(await comment.count() === 0, '重新登录没有静默发送评论')
  await tab.playwright.getByRole('button', {name:'发送评论',exact:true}).click()
  await comment.waitFor({state:'visible'})
  assert(await comment.count() === 1, '显式发送后只有一条评论')
  assert(await input.evaluate(element=>element.value) === '', '服务器确认后清空评论输入')
  await tab.reload()
  await comment.waitFor({state:'visible'})
  assert(await comment.count() === 1, '刷新后唯一评论仍存在')
  await fs.mkdir(outputDir, {recursive:true})
  await fs.writeFile(outputDir+'/comment-session-replay.jpg', await tab.screenshot({fullPage:false}))
  await fs.writeFile(outputDir+'/comment-session-results.json', JSON.stringify({checks,passed:checks.length,postId,text,date:'2026-10-22'},null,2))
  return checks
}
