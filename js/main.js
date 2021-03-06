var width = 40;//640;
var height = 30;//480;

var webCamWindow = document.getElementById("webCamWindow");
webCamWindow.style.width = width;
webCamWindow.style.height = height;

document.getElementById("preview").onclick = function(){
    webCamWindow.style.visibility = this.checked ? "visible" : "hidden";
};

var noiseThreshold = 20;

function diffPixel(p1, p2) {
    var rDiff = p1[0] - p2[0];
    var gDiff = p1[1] - p2[1];
    var bDiff = p1[2] - p2[2];

    if (Math.abs(rDiff < noiseThreshold))
        rDiff = 0;
    if (Math.abs(gDiff < noiseThreshold))
        gDiff = 0;
    if (Math.abs(bDiff < noiseThreshold))
        bDiff = 0;

    return rDiff * rDiff 
         + gDiff * gDiff 
         + bDiff * bDiff;
}

function State(width, height){
    this.__width = width;
    this.__height = height;
    this.__cx = new Array(2);
    this.__currentCx = 0;
    this.__filled = 0;
    
    for(var i = 0; i < this.__cx.length; ++i){
        var canvas = document.createElement("canvas");
        this.__cx[i] = canvas.getContext("2d");
    }
}

State.prototype.next = function(image){
    var curCx = this.__currentCx;
    var prevCx = this.__cx[curCx];
    if ( ++curCx == this.__cx.length )
        curCx = 0;
    var nextCx = this.__cx[curCx];
    this.__currentCx = curCx;

    nextCx.drawImage(image, 0, 0, this.__width, this.__height);

    if (this.__filled < this.__cx.length - 1){
        ++this.__filled;
        return 0;
    }

    var result = 0;
    for(var i = 0; i < this.__width; ++i)
        for(var j = 0; j < this.__height; ++j){
            var pixel1 = prevCx.getImageData(i, j, 1, 1);
            var pixel2 = nextCx.getImageData(i, j, 1, 1);
            result += diffPixel(pixel1.data, pixel2.data);
        }
    return result;
};

function startCamera(){
    var getUserMedia = navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia || navigator.msGetUserMedia;
    getUserMedia.call(
        navigator,
        {video: true},
        function(localMediaStream){
            var vendorURL = window.URL || window.webkitURL;

            if (getUserMedia != navigator.mozGetUserMedia)
                webCamWindow.src = vendorURL.createObjectURL(localMediaStream);
            else {
                webCamWindow.mozSrcObject = localMediaStream;
                webCamWindow.play();
            } 
        },
        console.error);
}

var requestAnimationFrame = window.requestAnimationFrame 
                         || window.webkitRequestAnimationFrame 
                         || window.mozRequestAnimationFrame 
                         || function(callback){
                                window.setTimeout(callback, 1000/60);
                            };

function run() {
    var wsProtocol = window.location.protocol == "https:" ? "wss:" : "ws:";
    var ws = new WebSocket(wsProtocol + "//" + window.location.host);

    startCamera();

    var state = new State(width, height);
    var toSend = [];

    function showStatus(msg){
        document.getElementById( "post_result" ).innerHTML = msg;
    }

    function step(){
        var result = state.next(webCamWindow);
        document.getElementById( "stat" ).innerHTML = 'result: ' + result;
        toSend.push( result );

        requestAnimationFrame(step);
    }

    function wsSend(){
        switch (ws.readyState){
            case 0:
                showStatus("WebSocket: connecting...");
                break;
            case 1:
                showStatus("WebSocket: OK");
                if (toSend.length){
                    ws.send(JSON.stringify(toSend));
                    toSend = [];
                }
                break;
            case 2:
                showStatus("WebSocket: closing");
                break;
            case 3:
                showStatus("WebSocket: closed");
                break;
            default:
                showStatus("WebSocket: unknown status " + ws.readyState);
                break;
        }
        window.setTimeout(wsSend, 100);
    }
    
    step();
    wsSend();
}

run();
