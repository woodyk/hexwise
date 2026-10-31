import AppKit
let folder=URL(fileURLWithPath:CommandLine.arguments[1],isDirectory:true)
try FileManager.default.createDirectory(at:folder,withIntermediateDirectories:true)
for (name,size) in [("icon_16x16",16),("icon_16x16@2x",32),("icon_32x32",32),("icon_32x32@2x",64),("icon_128x128",128),("icon_128x128@2x",256),("icon_256x256",256),("icon_256x256@2x",512),("icon_512x512",512),("icon_512x512@2x",1024)] {
    let n=CGFloat(size)
    let rep=NSBitmapImageRep(bitmapDataPlanes:nil,pixelsWide:size,pixelsHigh:size,bitsPerSample:8,samplesPerPixel:4,hasAlpha:true,isPlanar:false,colorSpaceName:.deviceRGB,bytesPerRow:0,bitsPerPixel:0)!
    NSGraphicsContext.saveGraphicsState();NSGraphicsContext.current=NSGraphicsContext(bitmapImageRep:rep)
    NSColor(calibratedRed:0.95,green:0.96,blue:0.91,alpha:1).setFill()
    NSBezierPath(roundedRect:NSRect(x:n*0.03,y:n*0.03,width:n*0.94,height:n*0.94),xRadius:n*0.2,yRadius:n*0.2).fill()
    let green=NSColor(calibratedRed:0.15,green:0.34,blue:0.25,alpha:1)
    green.setStroke();let hex=NSBezierPath();let points:[NSPoint]=[.init(x:n*0.3,y:n*0.82),.init(x:n*0.7,y:n*0.82),.init(x:n*0.86,y:n*0.63),.init(x:n*0.86,y:n*0.37),.init(x:n*0.7,y:n*0.18),.init(x:n*0.3,y:n*0.18),.init(x:n*0.14,y:n*0.37),.init(x:n*0.14,y:n*0.63)]
    hex.move(to:points[0]);for p in points.dropFirst(){hex.line(to:p)};hex.close();hex.lineWidth=n*0.035;hex.stroke()
    let attrs:[NSAttributedString.Key:Any]=[.font:NSFont.monospacedSystemFont(ofSize:n*0.47,weight:.semibold),.foregroundColor:green]
    ("H" as NSString).draw(at:NSPoint(x:n*0.32,y:n*0.2),withAttributes:attrs)
    NSColor(calibratedRed:0.78,green:0.57,blue:0.30,alpha:1).setFill();NSBezierPath(ovalIn:NSRect(x:n*0.67,y:n*0.47,width:n*0.075,height:n*0.075)).fill()
    NSGraphicsContext.restoreGraphicsState()
    try rep.representation(using:.png,properties:[:])!.write(to:folder.appendingPathComponent(name+".png"))
}
