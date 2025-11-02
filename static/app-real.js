// 简化前端逻辑示例（使用 ApiClient）
(function(){
  console.log('app-real loaded. ApiClient:', window.ApiClient ? 'available' : 'missing');
  // 示例：自动 ping 会话列表
  async function init(){
    try {
      const res = await ApiClient.listConversations(5);
      console.log('convs:', res);
    } catch(e){
      console.error('ApiClient error', e);
    }
  }
  window.addEventListener('load', init);
})();
