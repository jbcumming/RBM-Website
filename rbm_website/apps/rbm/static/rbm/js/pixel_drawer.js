// The pixel drawer javascript element that allows users to draw images
function PixelDrawer(drawerContainer, width, height, mode, max_labels, uploadURL, csrfToken) {
    // The canvas
    var canvas_object = new Canvas(width, height);
    var canvas = canvas_object.canvas;
    var container;

    // The drawing tools
    var brushes = {SMALL: 1, MEDIUM: 2, LARGE: 3};
    var currentlyDrawing = false;
    var blank = true;
    var tools = {PEN: 0, ERASER: 1};
    var currentTool = tools.PEN;

    createLayout();
    canvas_object.addCheckerboard();
    container.append(canvas);

    // Variables to store elements
    var usedClassNames = new Array();
    var download;
    var train;
    var classes_remaining;

    // If on the training page
    // Use the button to add classes
    // Otherwise use it to classify
    if (mode == "train") {
        classes_remaining = max_labels;
        printRemainingClasses();
        download = $('#addClass');
        download.click(function() {
            addClass();
        });
        createTrainButton();
    } else if (mode == "classify") {
        download = $('#classifyButton');
        download.click(function() {
            classify();
        });
    } else {

    }

    // The drawing function elements and tools
    var className = $('#className');
    var pen = $('#brush');
    var clear = $('#clear');
    var eraser = $('#eraser');
    var small = $('#small');
    var medium = $('#medium');
    var large = $('#large');
    var centre = $('#centre');

    // Disables certain attributes to start with
    pen.attr("disabled", true);
    clear.attr("disabled", true);
    small.attr("disabled", true);

    // Clears the canvas button
    clear.click(function() {
        clearCanvas();
    });

    // If the pen tool is clicked
    pen.click(function() {
        currentTool = tools.PEN;
        canvas_object.changeBrushSize(brushes.SMALL);
        pen.attr("disabled", true);
        eraser.attr("disabled", false);
        small.attr("disabled", true);
        medium.attr("disabled", false);
        large.attr("disabled", false);
    });

    // If the eraser is clicked
    eraser.click(function() {
        currentTool = tools.ERASER;
        eraser.attr("disabled", true);
        pen.attr("disabled", false);
        small.attr("disabled", true);
        medium.attr("disabled", true);
        large.attr("disabled", true);
    });

    // If the small size pen is clicked
    small.click(function() {
        canvas_object.changeBrushSize(brushes.SMALL);
        small.attr("disabled", true);
        medium.attr("disabled", false);
        large.attr("disabled", false);
    });

    // If the medium sized pen is clicked
    medium.click(function() {
        canvas_object.changeBrushSize(brushes.MEDIUM);
        small.attr("disabled", false);
        medium.attr("disabled", true);
        large.attr("disabled", false);
    });

    // If the large sized pen is clicked
    large.click(function() {
        canvas_object.changeBrushSize(brushes.LARGE);
        small.attr("disabled", false);
        medium.attr("disabled", false);
        large.attr("disabled", true);
    });

    // Implementes centre of gravity centering
    // This is key to make sure images are in the correct position
    // Performs mathematical calculations to find the centre
    centre.click(function() {
        var bounds = canvas_object.getCanvasBounds();
        var drawHeight = bounds["top"] - bounds["bottom"];
        var drawWidth = bounds["right"] - bounds["left"];
        var drawHeightCentre = bounds["bottom"] + Math.round(drawHeight/2);
        var drawWidthCentre = bounds["left"] + Math.round(drawWidth/2);
        var heightCentre = Math.round(height/2);
        var widthCentre = Math.round(width/2);

        var blackPixels = 0;
        var totalWidth = 0;
        var totalHeight = 0;
        var context = canvas_object.canvas[0].getContext('2d');
        var aspRatio = canvas_object.aspRatio;
        for (var col = 0; col < canvas_object.pixelWidth; col++) {
            for (var row = 0; row < canvas_object.pixelHeight; row++) {
                var pixData = context.getImageData(col*aspRatio, row*aspRatio, 1, 1);
                if (pixData.data[0] === 0) {
		    blackPixels++;
                    totalHeight += row;
                    totalWidth += col;
                }
            }
        }

        heightCog = Math.floor(totalHeight/blackPixels);
        widthCog  = Math.floor(totalWidth/blackPixels);
        heightOffset = heightCentre - heightCog;
        widthOffset  = widthCentre  - widthCog;
        canvas_object.shiftDrawing(-heightOffset, widthOffset);
    });

   // Creates the drawing tool
   function createLayout() {
        container = $('<div/>', {
            id: 'canvasContainer',
        }).appendTo(drawerContainer);
    }

    // Prints the classes remaining
    function printRemainingClasses() {
        $('#classesRemainingDisplay').empty().prepend(classes_remaining + ' out of ' + max_labels + ' classes remaining!');
    }

    // The classify function
    // Gets the picture and uploads it to the server via AJAX
    // Deals with the return JSON of probability
    function classify() {
        previewCanvas = canvas_object.generatePreview();
        imageURL = previewCanvas.toDataURL("image/png");

        $.post(uploadURL, {'image_data' : imageURL, csrfmiddlewaretoken : csrfToken}, function(data, textStatus, xhr) {
            $('#maxProbContainer').text(data.result);
            for (var i = 0; i < max_labels; i++) {
		var rounded_number = (parseFloat(data.probs[i]) * 100 ).toFixed(3);
		if(data.label_values[i] == data.result){
			$('#' + data.label_values[i] + 'LabelContainer').parent().css('background-color', '#4cae4c');
		} else {
			$('#' + data.label_values[i] + 'LabelContainer').parent().css('background-color', 'white');
		}

                $('#' + data.label_values[i] + 'LabelContainer').text(rounded_number + '%');
            };
        });
    }

    // Creates the training button
    // Gets all images and names from the HTML classes
    // Posts the data to the server for training
    function createTrainButton() {
        train = $('#trainButton');
        train.attr("disabled", true);
        train.click(function() {
            var images = [];

            $('.imageClass').each(function() {
                var classImg = $(this).children("img");
                var data = {
                    'image_name': classImg.prop('id'),
                    'image_data' : classImg.prop('src')
                };
                images.push(data);
            });

            $.post(uploadURL, {
                classImages: images,
                pre_epoch: $('#pre_epoch').val(),
                train_epoch: $('#train_epoch').val(),
                train_loop: $('#train_loop').val(),

                csrfmiddlewaretoken: csrfToken
            }, function(data, textStatus, xhr) {
                window.location.href = '/rbm/training/';
            });
        });
    }

    // Adds a class of images to the layer
    // Checks to make sure all requirements are satisfied
    // Gets the image from the canvas
    // Creates an image to show on the page
    // Puts the element on the HTML page
    function addClass() {
        var previewCanvas = canvas_object.generatePreview();
        var imageURL = previewCanvas.toDataURL("image/png");
        var imageID = className.val();
        var index = $.inArray(imageID, usedClassNames);

        if (imageID === "") {
            topBar("Please enter a class name before adding a class!", 5000, 'error');
        } else if (index != -1) {
            topBar("The class name \'" + imageID + "\' has already been used!", 5000, 'error');
        } else if (imageID.indexOf(' ') >= 0) {
	    topBar("Class names cannot contains spaces! Please re-write it!", 5000, 'error');
	} else {
            image = $('<img style="border: 1px solid #000000;" id="' + imageID + '" src="' +  imageURL + '" >');
            deleteButton = $('<input type="button" value="-" />');
            deleteButton.click(function() {
                var index = usedClassNames.indexOf(imageID);
                usedClassNames.splice(index, 1);
                classes_remaining++;
                if (classes_remaining == 1) {
                    $('#trainButton').attr("disabled", true);
                    $('#addClass').attr("disabled", false);
                    $('#className').attr("disabled", false);
                }
                printRemainingClasses();
                $(this).parent().fadeOut(300, function() { $(this).remove(); });
            });
            div = $('<div class="imageClass"></div>');

            div.append(deleteButton);
            div.append('  ');
            div.append(image);
            div.append(' - ' + imageID);

            clearCanvas();
            className.val('');
            classes_remaining--;
            usedClassNames.push(imageID);
            div.hide().appendTo('#imageClasses').fadeIn(400);
            printRemainingClasses();
            if (classes_remaining === 0) {
                $('#addClass').attr("disabled", true);
                $('#className').attr("disabled", true);
                $('#trainButton').attr("disabled", false);
            }
        }
    }

    // If the mouse is down, draw
    canvas.mousedown(draw);

    // If the mouse moves, re draw
    canvas.mousemove( function (e) {
        if (currentlyDrawing) {
            draw(e);
        }
    });

    // Clears the canvas of all drawings
    function clearCanvas() {
        canvas_object.addCheckerboard();
        blank = true;
        clear.attr("disabled", true);
    }

    // Draws on the canvas at the given co-ordinates
    function draw(e){
        var offset = canvas.offset();
        x = Math.floor((e.pageX - offset.left) / canvas_object.aspRatio);
        y = Math.floor((e.pageY - offset.top) / canvas_object.aspRatio);

        switch(currentTool) {
            case tools.PEN:
                canvas_object.draw(x, y);
                if (blank) {
                    clear.attr("disabled", false);
                }
                blank = false;
                break;
            case tools.ERASER:
                canvas_object.erase(x, y);
                break;
        }

        currentlyDrawing = true;
    }

    canvas.mouseup( function (event) {
        currentlyDrawing = false;
    });

    canvas.mouseleave( function (event) {
        currentlyDrawing = false;
    });
}

// Creates the drawing canvas
function Canvas(pixelWidth, pixelHeight){
    var aspRatio = 10;
    this.aspRatio = aspRatio;
    this.brushSize = 1;
    this.pixelWidth = pixelWidth
    this.pixelHeight = pixelHeight

    var colours = {GREY: "#DEDDDC", BLACK: "#000000", WHITE:"#FFFFFF"};
    var size = {SMALL: 1, MEDIUM: 2, LARGE: 3};

    var canvasWidth = aspRatio * pixelWidth;
    var canvasHeight = aspRatio * pixelHeight;

    this.canvas = createCanvas(canvasWidth, canvasHeight);

    var context = this.canvas[0].getContext("2d");

    /* Public Functions */
    this.draw = function(x, y) {
        if (this.brushSize >= size.SMALL) {
            fillPixel(colours.BLACK, x, y);
        }
        if (this.brushSize >= size.MEDIUM) {
            fillPixel(colours.BLACK, x+1, y);
            fillPixel(colours.BLACK, x-1, y);
            fillPixel(colours.BLACK, x, y+1);
            fillPixel(colours.BLACK, x, y-1);
        }
        if (this.brushSize >= size.LARGE) {
            fillPixel(colours.BLACK, x+1, y+1);
            fillPixel(colours.BLACK, x-1, y+1);
            fillPixel(colours.BLACK, x-1, y-1);
            fillPixel(colours.BLACK, x+1, y-1);
        }
    };

    this.erase = function(x, y) {
        fillCheckerboardPiece(x, y);
    };

    this.shiftDrawing = function(heightOffset, widthOffset) {
        var tempCanvas = createCanvas(canvasWidth, canvasHeight);
        var tempCtx = tempCanvas[0].getContext("2d");
        tempCtx.drawImage(this.canvas[0], 0, 0);
        this.addCheckerboard();

        for (var col = 0; col < pixelWidth; col++) {
            for (var row = 0; row < pixelHeight; row++) {
                var pixData = tempCtx.getImageData(col*aspRatio, row*aspRatio, 1, 1);
                if (pixData.data[0] === 0) {
                    context.fillStyle = colours.BLACK;
                    context.fillRect((col+widthOffset)*aspRatio, (row-heightOffset)*aspRatio, aspRatio, aspRatio);
                }
            }
        }
    };

    this.generatePreview = function() {
        previewCanvas = createCanvas(pixelWidth, pixelHeight);

        var previewContext = previewCanvas[0].getContext("2d");
        for (var col = 0; col < pixelWidth; col++) {
            for (var row = 0; row < pixelHeight; row++) {
                var pixData = context.getImageData(col*aspRatio, row*aspRatio, 1, 1);
                if (pixData.data[0] === 0) {
                    previewContext.fillStyle = colours.BLACK;
                } else {
                    previewContext.fillStyle = colours.WHITE;
                }
                previewContext.fillRect(col, row, 1, 1);
            }
        }
        return previewCanvas[0];
    };

    this.getCanvasBounds = function() {
        var left = pixelWidth + 1;
        var right = -1;
        var bottom = -1;
        var top = pixelHeight + 1;
        for (var col = 0; col < pixelWidth; col++) {
            for (var row = 0; row < pixelHeight; row++) {
                var pixData = context.getImageData(col*aspRatio, row*aspRatio, 1, 1);
                if (pixData.data[0] === 0) {
                    if  (col > right) {
                        right = col;
                    }
                    if (col < left) {
                        left = col;
                    }
                    if (row > bottom) {
                        bottom = row;
                    }
                    if (row < top) {
                        top = row;
                    }
                }
            }
        }
        bottom = pixelHeight - (bottom + 1);
        top = pixelHeight - (top + 1);
        return ({"left": left, "right": right, "bottom": bottom, "top": top});
    };

    this.addCheckerboard = function() {
    for (var col = 0; col < pixelWidth; col++) {
            for (var row = 0; row < pixelHeight; row++) {
                fillCheckerboardPiece(col, row);
            }
        }
    };

    this.changeBrushSize = function(newSize) {
        this.brushSize = newSize;
    }

    /* Private Functions */
    function createCanvas(canvasWidth, canvasHeight){
        var canvas = $('<canvas/>', {
            'style' : 'position: relative; border: 1px solid;',
            'width' : canvasWidth,
            'height' : canvasHeight
        });
        canvas[0].width = canvasWidth;
        canvas[0].height= canvasHeight;
        return canvas;
    }

    function fillPixel(colour, x, y) {
        context.fillStyle = colour;
        context.fillRect(x*aspRatio, y*aspRatio, aspRatio, aspRatio);
    }

    function fillCheckerboardPiece(x,y) {
        if (x%2 === 0) {
            if (y%2 === 0) {
                fillPixel(colours.GREY, x, y);
            } else {
                fillPixel(colours.WHITE, x, y);
            }
        } else {
            if (y%2 == 1) {
                fillPixel(colours.GREY, x, y);
            } else {
                fillPixel(colours.WHITE, x, y);
            }
        }
    }
}
