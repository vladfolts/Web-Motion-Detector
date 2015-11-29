var width = 40;//640;
var height = 30;//480;

var webCamWindow = document.getElementById("webCamWindow");
webCamWindow.style.width = width;
webCamWindow.style.height = height;

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
    startCamera();

    var state = new State(width, height);
    var toSend = [];

    function post(){
        $.post("data", 
               JSON.stringify(toSend))
         .done(function(data, status){
                    document.getElementById( "post_result" ).innerHTML = "POST data: OK";
                    window.setTimeout(post, 100);
                })
         .fail(function(){
                    toSend = [];
                    document.getElementById( "post_result" ).innerHTML = "POST data: failed";
                    window.setTimeout(post, 1000);
                });

        toSend = [];
    }

    function step(){
        var result = state.next(webCamWindow);
        document.getElementById( "stat" ).innerHTML = 'result: ' + result;
        toSend.push( result );

        requestAnimationFrame(step);
    }

    step();
    post();
}

run();
