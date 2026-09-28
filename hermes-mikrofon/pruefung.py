from playwright.sync_api import sync_playwright
EXE="/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
B="http://localhost:8941/"

STUB = """
window.__belegt=false; window.__abort=0; window.__starts=0; window.__wirf=null;
class FakeSR{
  constructor(){this.onresult=null;this.onerror=null;this.onend=null;}
  start(){ if(window.__wirf){const e=new Error(window.__wirf);e.name='InvalidStateError';throw e;}
    window.__starts++; window.__belegt=true;
    if(window.__endeSofort){setTimeout(()=>{this.onend&&this.onend();},20);}
    else setTimeout(()=>{ this.onresult&&this.onresult({resultIndex:0,
      results:[Object.assign([{transcript:'hallo hermes'}],{isFinal:true})]});},30);}
  stop(){window.__belegt=false; setTimeout(()=>{this.onend&&this.onend();},5);}
  abort(){window.__abort++; window.__belegt=false;}
}
window.SpeechRecognition=FakeSR; window.webkitSpeechRecognition=FakeSR;
"""
ERG=[]
def pruef(name, bedingung, detail=""):
    ERG.append((name, bool(bedingung), detail))

def neu(b, seite, vor=""):
    pg=b.new_page(); pg.add_init_script(STUB + vor); pg.goto(B+seite); pg.wait_for_timeout(250); return pg

def verstecken(pg):
    pg.evaluate("Object.defineProperty(document,'visibilityState',{get:()=>'hidden',configurable:true});"
                "Object.defineProperty(document,'hidden',{get:()=>true,configurable:true});"
                "document.dispatchEvent(new Event('visibilitychange'))")

with sync_playwright() as p:
    b=p.chromium.launch(executable_path=EXE)

    # 1-3 Grundzustand
    pg=neu(b,"einfach.html"); k=pg.locator(".mikrofon-knopf")
    pruef("Knopf wird eingefügt", k.count()==1)
    pruef("Knopf ist bedienbar", not k.is_disabled())
    gr=pg.evaluate("(()=>{const r=document.querySelector('.mikrofon-knopf').getBoundingClientRect();return [Math.round(r.width),Math.round(r.height)]})()")
    pruef("Fingerfläche mind. 44px", min(gr)>=44, f"{gr[0]}x{gr[1]}")
    pruef("Auto-Knopf vorhanden", pg.locator(".auto-knopf").count()==1)

    # 4-6 Diktat einfaches Feld
    k.click(); pg.wait_for_timeout(200)
    pruef("Zuhören startet", "hoert" in (k.get_attribute("class") or ""))
    pruef("Mikrofon belegt während Zuhören", pg.evaluate("window.__belegt"))
    pruef("Text landet im Feld", pg.locator("#input").input_value()=="hallo hermes")
    pg.wait_for_timeout(700)
    pruef("Auto-Senden feuert", pg.evaluate("window.__gesendet")==1)
    pruef("Mikrofon nach Auto-Senden frei", not pg.evaluate("window.__belegt"))

    # 7 zweites Diktat hängt an
    k.click(); pg.wait_for_timeout(200); k.click(); pg.wait_for_timeout(100)
    pruef("Zweites Diktat hängt an", pg.locator("#input").input_value()=="hallo hermes hallo hermes")

    # 8 getippt löst nichts aus
    pg2=neu(b,"einfach.html")
    pg2.locator("#input").fill("von Hand"); pg2.wait_for_timeout(900)
    pruef("Getippter Text sendet nicht", pg2.evaluate("window.__gesendet")==0)

    # 9-10 Auto aus
    pg3=neu(b,"einfach.html"); k3=pg3.locator(".mikrofon-knopf"); a3=pg3.locator(".auto-knopf")
    a3.click()
    pruef("Auto lässt sich ausschalten", a3.get_attribute("aria-pressed")=="false")
    k3.click(); pg3.wait_for_timeout(900)
    pruef("Auto aus: kein Senden", pg3.evaluate("window.__gesendet")==0)
    pg3.reload(); pg3.wait_for_timeout(250)
    pruef("Einstellung übersteht Neuladen", pg3.locator(".auto-knopf").get_attribute("aria-pressed")=="false")

    # 11-12 Framework-Feld
    pg4=neu(b,"gesteuert.html"); k4=pg4.locator(".mikrofon-knopf")
    k4.click(); pg4.wait_for_timeout(250)
    pruef("Framework-Feld: Text kommt an", pg4.evaluate("window.__zustand")=="hallo hermes")
    pg4.wait_for_timeout(700)
    pruef("Framework-Feld: gesendet", pg4.evaluate("window.__gesendet")==1)

    # 13-14 verweigerndes Feld
    pg5=neu(b,"starr.html"); k5=pg5.locator(".mikrofon-knopf")
    k5.click(); pg5.wait_for_timeout(900)
    pruef("Verweigerndes Feld: sichtbarer Hinweis",
          "nicht übernommen" in (pg5.locator("#mikrofon-hinweis").inner_text() if pg5.locator("#mikrofon-hinweis").count() else ""))
    pruef("Verweigerndes Feld: keine leere Nachricht", pg5.evaluate("window.__gesendet")==0)

    # 15-16 Hintergrund
    pg6=neu(b,"einfach.html"); k6=pg6.locator(".mikrofon-knopf")
    k6.click(); pg6.wait_for_timeout(150); verstecken(pg6); pg6.wait_for_timeout(250)
    pruef("Hintergrund: Mikrofon freigegeben", not pg6.evaluate("window.__belegt"))
    pruef("Hintergrund: abort() benutzt", pg6.evaluate("window.__abort")>=1)
    pruef("Hintergrund: Zuhören beendet", "hoert" not in (k6.get_attribute("class") or ""))

    # 17 Dauerschleife
    pg7=neu(b,"einfach.html", "window.__endeSofort=true;"); k7=pg7.locator(".mikrofon-knopf")
    k7.click(); pg7.wait_for_timeout(3000)
    pruef("Dauerschleife gedeckelt", not pg7.evaluate("window.__belegt"),
          f"{pg7.evaluate('window.__starts')} Starts")
    pruef("Dauerschleife: Zuhören beendet", "hoert" not in (k7.get_attribute("class") or ""))

    # 18 Notbremse
    pg8=neu(b,"einfach.html", "window.__endeSofort=false;")
    pg8.evaluate("window.__still=true")
    k8=pg8.locator(".mikrofon-knopf")
    pg8.evaluate("window.__wirf=null")
    k8.click(); pg8.wait_for_timeout(2200)
    pruef("Notbremse gibt frei", not pg8.evaluate("window.__belegt"))

    # 19 Fehlerfall
    pg9=neu(b,"einfach.html")
    pg9.locator(".mikrofon-knopf").click(); pg9.wait_for_timeout(100)
    pg9.evaluate("document.querySelector('.mikrofon-knopf'); "
                 "window.__belegt=true;")
    pg9.evaluate("(()=>{const o=Object.values(window); })()")
    # Fehler ueber den Erkenner ausloesen
    pg9.evaluate("""(()=>{ const ev={error:'not-allowed'};
        const alle=performance.getEntries; })()""")
    # 20 Start wirft InvalidStateError -> abort erzwungen
    pg10=neu(b,"einfach.html", "window.__wirf='läuft schon';")
    pg10.locator(".mikrofon-knopf").click(); pg10.wait_for_timeout(200)
    pruef("Start wirft: abort() erzwungen", pg10.evaluate("window.__abort")>=1)
    pruef("Start wirft: Anzeige zurückgesetzt",
          "hoert" not in (pg10.locator(".mikrofon-knopf").get_attribute("class") or ""))
    pruef("Start wirft: Hinweis sichtbar", pg10.locator("#mikrofon-hinweis").count()==1)
    b.close()

n=len(ERG); ok=sum(1 for _,g,_ in ERG if g)
print(f"{'':2} {'Prüfung':<44} Ergebnis")
print("-"*70)
for name,gut,det in ERG:
    print(f"   {name:<44} {'bestanden' if gut else 'FEHLER':<10} {det}")
print("-"*70)
print(f"   {ok} von {n} bestanden")
