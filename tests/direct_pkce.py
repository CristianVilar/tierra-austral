import json,re
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch();c=b.new_context(locale='es-CL');pg=c.new_page()
    seen={}
    def tok(route):
        seen['body']=route.request.post_data
        route.fulfill(status=200,content_type='application/json',body=json.dumps({"access_token":"a.b.c","refresh_token":"r","expires_in":3600,"token_type":"bearer","user":{"id":"u1","email":"x@y.z"}}))
    c.route("**/auth/v1/token*",tok)
    c.route("**/rest/v1/**",lambda r:r.fulfill(status=200,content_type='application/json',body='[]'))
    c.route("**/auth/v1/user*",lambda r:r.fulfill(status=200,content_type='application/json',body=json.dumps({"id":"u1","email":"x@y.z"})))
    c.add_init_script("""window.supabase={createClient:()=>({auth:{storageKey:'ta-auth',storage:{setItem(){},getItem(){return null}},onAuthStateChange(){},
      async setSession(x){throw new Error('lib roto')},async exchangeCodeForSession(){return {error:{message:'PKCE code verifier not found in storage'}}},async getSession(){return {data:{session:null}}}},
      from(){return {select:async()=>({data:[],error:null})}},channel(){return {on(){return this},subscribe(){return this}}}})};""")
    pg.goto('file:///home/claude/tierra-austral/index.html')
    pg.evaluate("localStorage.setItem('ta-pkce','VERIFIER123');localStorage.setItem('ta-oauth','1')")
    pg.goto('file:///home/claude/tierra-austral/index.html?code=abc')
    pg.wait_for_timeout(4000)
    print(seen, pg.evaluate("[AUTH.user&&AUTH.user.email,AUTH.bootErr,AUTH.bootRaw]"))
    b.close()
