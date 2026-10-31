import Cocoa
import WebKit

final class HexwiseApp: NSObject, NSApplicationDelegate, NSWindowDelegate, WKNavigationDelegate, WKUIDelegate, WKScriptMessageHandler {
    var window: NSWindow!
    var web: WKWebView!
    var backend: Process?
    var serverOrigin = ""
    var scopedURLs: [URL] = []

    func applicationDidFinishLaunching(_ notification: Notification) {
        let app = NSApplication.shared
        app.setActivationPolicy(.regular)
        buildMenu()
        window = NSWindow(contentRect: NSRect(x: 0,y: 0,width: 1510,height: 970),
                          styleMask: [.titled,.closable,.miniaturizable,.resizable],backing: .buffered,defer: false)
        window.title = "Hexwise"
        window.delegate = self
        window.minSize = NSSize(width: 1100,height: 720)
        window.center()
        let config = WKWebViewConfiguration()
        config.preferences.setValue(true,forKey:"developerExtrasEnabled")
        config.userContentController.add(self,name:"openFile")
        config.userContentController.add(self,name:"openFolder")
        web = WKWebView(frame: window.contentView!.bounds,configuration: config)
        web.autoresizingMask = [.width,.height]
        web.navigationDelegate = self
        web.uiDelegate = self
        window.contentView!.addSubview(web)
        window.makeKeyAndOrderFront(nil)
        app.activate(ignoringOtherApps: true)
        startBackend()
    }

    func startBackend() {
        guard let resources = Bundle.main.resourceURL else { return }
        let source = resources.appendingPathComponent("app/server.py")
        let candidates = [ProcessInfo.processInfo.environment["HEXWISE_PYTHON"] ?? "", "/opt/homebrew/bin/python3", "/usr/local/bin/python3", "/usr/bin/python3"]
        guard let python = candidates.first(where: { !$0.isEmpty && FileManager.default.isExecutableFile(atPath: $0) }) else {
            fail("Python 3.9 or newer is required. Install Python 3, then reopen Hexwise."); return
        }
        let data = FileManager.default.urls(for:.applicationSupportDirectory,in:.userDomainMask)[0].appendingPathComponent("Hexwise")
        let workspace = data.appendingPathComponent("Workspace")
        do { try FileManager.default.createDirectory(at:workspace,withIntermediateDirectories:true) } catch { fail("Cannot create the Hexwise workspace."); return }
        let pipe = Pipe()
        let process = Process()
        process.executableURL = URL(fileURLWithPath:python)
        process.arguments = [source.path,"--no-browser","--workspace",workspace.path,"--data-dir",data.path]
        process.environment = ProcessInfo.processInfo.environment.merging(["PYTHONDONTWRITEBYTECODE":"1"]) { _,new in new }
        process.currentDirectoryURL = workspace
        process.standardOutput = pipe
        process.standardError = FileHandle.nullDevice
        backend = process
        do { try process.run() } catch { fail("The local application service could not start."); return }
        DispatchQueue.global().async { [weak self] in
            var data = Data()
            while !data.contains(10) {
                let chunk = pipe.fileHandleForReading.availableData
                if chunk.isEmpty { break }
                data.append(chunk)
            }
            guard let line = String(data:data,encoding:.utf8)?.split(separator:"\n").first,
                  let url = URL(string:String(line)), url.host == "127.0.0.1" else {
                DispatchQueue.main.async { self?.fail("The local service did not start. Python 3.9 or newer is required.") }; return
            }
            DispatchQueue.main.async {
                self?.serverOrigin = "http://127.0.0.1:\(url.port ?? 0)"
                self?.web.load(URLRequest(url:url))
            }
        }
    }

    func fail(_ message:String) {
        let alert = NSAlert(); alert.messageText = "Hexwise needs your attention"; alert.informativeText = message; alert.runModal()
    }

    func buildMenu() {
        let main = NSMenu()
        let appItem = NSMenuItem(); main.addItem(appItem)
        let appMenu = NSMenu(); appItem.submenu = appMenu
        appMenu.addItem(withTitle:"About Hexwise",action:#selector(about),keyEquivalent:"")
        appMenu.addItem(NSMenuItem.separator())
        appMenu.addItem(withTitle:"Quit Hexwise",action:#selector(NSApplication.terminate(_:)),keyEquivalent:"q")
        let fileItem = NSMenuItem(); fileItem.title="File"; main.addItem(fileItem)
        let file = NSMenu(title:"File"); fileItem.submenu=file
        add(file,"Open File…",#selector(openFile),"o")
        add(file,"Open Folder…",#selector(openFolder),"")
        add(file,"New Application…",#selector(newApplication),"n")
        add(file,"Save Candidate",#selector(saveCandidate),"s")
        add(file,"Export Candidate…",#selector(exportCandidate),"")
        let editItem=NSMenuItem();editItem.title="Edit";main.addItem(editItem)
        let edit=NSMenu(title:"Edit");editItem.submenu=edit
        edit.addItem(withTitle:"Undo",action:Selector(("undo:")),keyEquivalent:"z")
        edit.addItem(withTitle:"Cut",action:#selector(NSText.cut(_:)),keyEquivalent:"x")
        edit.addItem(withTitle:"Copy",action:#selector(NSText.copy(_:)),keyEquivalent:"c")
        edit.addItem(withTitle:"Paste",action:#selector(NSText.paste(_:)),keyEquivalent:"v")
        edit.addItem(withTitle:"Select All",action:#selector(NSText.selectAll(_:)),keyEquivalent:"a")
        let viewItem=NSMenuItem();viewItem.title="View";main.addItem(viewItem)
        let view=NSMenu(title:"View");viewItem.submenu=view
        add(view,"Command Palette…",#selector(commands),"k")
        add(view,"Web Inspector Help…",#selector(developerTools),"")
        NSApplication.shared.mainMenu=main
    }
    func add(_ menu:NSMenu,_ title:String,_ action:Selector,_ key:String) { let item=NSMenuItem(title:title,action:action,keyEquivalent:key);item.target=self;menu.addItem(item) }
    func js(_ code:String) { web?.evaluateJavaScript("Promise.resolve((async()=>{\(code)})()).catch(e=>toast(e.message,true))",completionHandler:nil) }
    func jsString(_ value:String)->String { String(data:try! JSONEncoder().encode(value),encoding:.utf8)! }
    func userContentController(_ controller:WKUserContentController,didReceive message:WKScriptMessage) {
        guard message.frameInfo.isMainFrame,let url=message.frameInfo.request.url,url.scheme=="http",url.host=="127.0.0.1",
              "http://127.0.0.1:\(url.port ?? 0)"==serverOrigin else { return }
        if message.name=="openFile" { openFile() }
        if message.name=="openFolder" { openFolder() }
    }
    func retainAccess(_ url:URL) { if url.startAccessingSecurityScopedResource() { scopedURLs.append(url) } }
    @objc func openFile() {
        let panel=NSOpenPanel();panel.canChooseFiles=true;panel.canChooseDirectories=false
        if panel.runModal() == .OK,let url=panel.url { retainAccess(url);js("await openFile(\(jsString(url.path))); ") }
    }
    @objc func openFolder() {
        let panel=NSOpenPanel();panel.canChooseFiles=false;panel.canChooseDirectories=true
        if panel.runModal() == .OK,let url=panel.url { retainAccess(url);js("await browse(\(jsString(url.path))); ") }
    }
    @objc func newApplication() { js("await runAction('new');") }
    @objc func saveCandidate() { js("await stage();") }
    @objc func exportCandidate() { js("await runAction('export');") }
    @objc func commands() { js("commandPalette();") }
    @objc func developerTools() { let alert=NSAlert();alert.messageText="Web Inspector";alert.informativeText="Control-click the application interface and choose Inspect Element to open WebKit’s developer tools. Candidate previews use an isolated frame; inspected application pages have access to the current local session.";alert.runModal() }
    @objc func about() { let alert=NSAlert();alert.messageText="Hexwise Studio 0.2";alert.informativeText="Architecture-aware binary development.\nConcept: Wadih Frederick Khairallah — 2b0n2b!!!\nAI-assisted implementation.";alert.runModal() }
    func windowShouldClose(_ sender:NSWindow)->Bool { NSApplication.shared.terminate(sender); return false }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender:NSApplication)->Bool { true }
    func applicationShouldTerminate(_ sender:NSApplication)->NSApplication.TerminateReply {
        if serverOrigin.isEmpty { return .terminateNow }
        web.callAsyncJavaScript("return typeof canLeave === 'function' ? await canLeave() : true", arguments:[:],in:nil,in:.page) { result in
            switch result {
            case .success(let value): sender.reply(toApplicationShouldTerminate:(value as? Bool) == true)
            case .failure: sender.reply(toApplicationShouldTerminate:true)
            }
        }
        return .terminateLater
    }
    func applicationWillTerminate(_ notification:Notification) { backend?.terminate();for url in scopedURLs { url.stopAccessingSecurityScopedResource() } }

    func webView(_ webView:WKWebView,decidePolicyFor navigationAction:WKNavigationAction,decisionHandler:@escaping(WKNavigationActionPolicy)->Void) {
        guard let url=navigationAction.request.url else { decisionHandler(.cancel);return }
        if url.scheme=="about" || (url.host=="127.0.0.1" && "http://127.0.0.1:\(url.port ?? 0)"==serverOrigin) { decisionHandler(.allow);return }
        if navigationAction.navigationType == .linkActivated && ["https","http"].contains(url.scheme ?? "") { NSWorkspace.shared.open(url) }
        decisionHandler(.cancel)
    }
    func webView(_ webView:WKWebView,createWebViewWith configuration:WKWebViewConfiguration,for navigationAction:WKNavigationAction,windowFeatures:WKWindowFeatures)->WKWebView? {
        if let url=navigationAction.request.url,["https","http"].contains(url.scheme ?? "") { NSWorkspace.shared.open(url) };return nil
    }
    func webView(_ webView:WKWebView,runJavaScriptAlertPanelWithMessage message:String,initiatedByFrame frame:WKFrameInfo,completionHandler:@escaping()->Void) { let alert=NSAlert();alert.messageText=message;alert.runModal();completionHandler() }
    func webView(_ webView:WKWebView,runJavaScriptConfirmPanelWithMessage message:String,initiatedByFrame frame:WKFrameInfo,completionHandler:@escaping(Bool)->Void) { let alert=NSAlert();alert.messageText=message;alert.addButton(withTitle:"Continue");alert.addButton(withTitle:"Cancel");completionHandler(alert.runModal() == .alertFirstButtonReturn) }
    func webView(_ webView:WKWebView,runJavaScriptTextInputPanelWithPrompt prompt:String,defaultText:String?,initiatedByFrame frame:WKFrameInfo,completionHandler:@escaping(String?)->Void) { let alert=NSAlert();alert.messageText=prompt;let field=NSTextField(frame:NSRect(x:0,y:0,width:380,height:24));field.stringValue=defaultText ?? "";alert.accessoryView=field;alert.addButton(withTitle:"Continue");alert.addButton(withTitle:"Cancel");completionHandler(alert.runModal() == .alertFirstButtonReturn ? field.stringValue:nil) }
}

let app=NSApplication.shared
let delegate=HexwiseApp()
app.delegate=delegate
app.run()
