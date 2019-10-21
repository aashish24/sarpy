    dL = L.tileLayer('https://a.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>, Tiles courtesy of <a href="http://hot.openstreetmap.org/" target="_blank">Humanitarian OpenStreetMap Team</a>',
    maxZoom: 24,
    });

    var CustomCRS = L.CRS.XY = L.Util.extend({}, L.CRS.Simple, {
        transformation: new L.Transformation(1, 0, 1, 0)
    });

    var mymap = new L.map('mapid', {
        zoomControl: true,
        zoom: 4,
        crs: CustomCRS,
        minZoom: -5
        // layers: [dL],
    });

    var options = {
        position: 'topleft',
        drawMarker: false,
        drawPolyline: false,
        drawRectangle: true,
        drawPolygon: false,
        drawCircle: false,
        cutPolygon: false,
        editMode: true,
        removalMode: true,
    };

    mymap.pm.addControls(options);

    mymap.pm.Draw.options.hintlineStyle = {
        color: 'blue',
        dashArray: '5,5'
    };

    mymap.panTo([0.0, 0.0]);
    map_size = mymap.getSize();

    overlay = null;
    decimation = 0;
    raw_nx = 0;
    raw_ny = 0;


    function sanitizeBounds(xmin, ymin, xmax, ymax) {
        if (xmin < 0){
            xmin = 0;
        }
        if (ymin < 0) {
            ymin = 0;
        }
        if (xmax > raw_nx) {
            xmax = raw_nx;
        }
        if (ymax > raw_ny){
            ymax = raw_ny;
        }
        return [xmin, ymin, xmax, ymax]
    }
    mymap.on('moveend', function() {
        let xmax = mymap.getBounds().getEast();
        let xmin = mymap.getBounds().getWest();
        let ymax = mymap.getBounds().getNorth();
        let ymin = mymap.getBounds().getSouth();
        console.log(mymap.getBounds());

        sbounds = sanitizeBounds(xmin, ymin, xmax, ymax);

        cropImage(sbounds[0], sbounds[1], sbounds[2], sbounds[3]);

    });

    mymap.on('mousemove',
        function(e){
            var coord = e.latlng.toString().split(',');
            var lat = coord[0].split('(');
            var lng = coord[1].split(')');
            document.getElementById('pixel_y').value = lat[1]
            document.getElementById('pixel_x').value = lng[0]
        });

    let load_image = document.getElementById('load_image');
    load_image.addEventListener('click', updateImagePath);

    let ortho_image = document.getElementById('ortho_image');
    ortho_image.addEventListener('click', orthoImage);

    function b64toBlob(b64Data, contentType, sliceSize) {
        contentType = contentType || '';
        sliceSize = sliceSize || 512;

        var byteCharacters = atob(b64Data);
        var byteArrays = [];

        for (var offset = 0; offset < byteCharacters.length; offset += sliceSize) {
            var slice = byteCharacters.slice(offset, offset + sliceSize);

            var byteNumbers = new Array(slice.length);
            for (var i = 0; i < slice.length; i++) {
                byteNumbers[i] = slice.charCodeAt(i);
            }

            var byteArray = new Uint8Array(byteNumbers);

            byteArrays.push(byteArray);
        }

        var blob = new Blob(byteArrays, {type: contentType});
        return blob;
    }

    function updateImageOverlay() {

        let xhr = new XMLHttpRequest();
        let data = new FormData();

        xhr.open('POST', 'get_frame');
        xhr.setRequestHeader("X-CSRFToken", token);
        xhr.send(data);

        xhr.onload = function(evt) {
            let resp;
            try {
                resp = JSON.parse(xhr.response);
                let contentType = 'image/png';
                let blob = b64toBlob(resp.output_value.raster, contentType);
                let blobUrl = URL.createObjectURL(blob);

                let imageBounds = JSON.parse(resp.output_value.extent);
                let current_decimation = resp.output_value.decimation;
                let dec = document.getElementById('decimation_indicator');

                dec.value = current_decimation;
                decimation = current_decimation;

                if (overlay !== null) {
                    mymap.removeLayer(overlay);
                }

                let fit_flag = false;
                if (overlay === null) {
                    fit_flag = true;
                }
                overlay = L.imageOverlay(blobUrl, imageBounds);
                overlay.addTo(mymap);

                if (fit_flag) {
                    mymap.fitBounds(imageBounds);
                }

            } catch (error) {
                console.error(error);
            }
        }
    }

    function updateImagePath() {
        let image_path = document.getElementById('image_path');
        console.log(image_path)

        let xhr = new XMLHttpRequest();
        console.log(token)

        let data = new FormData();
        data.append('image_path', image_path.value);
        data.append('tny', map_size.y);
        data.append('tnx', map_size.x);

        xhr.open('POST', 'update_image_path');
        xhr.setRequestHeader("X-CSRFToken", token);
        console.log(data)
        xhr.send(data);

        console.log(map_size.y);
        console.log(map_size.x);

        xhr.onload = function(evt) {
            let resp;
            try {
                console.log(xhr.response)
                resp = JSON.parse(xhr.response);
                raw_nx = resp.nx;
                raw_ny = resp.ny;

                updateImageOverlay();

            } catch (error) {
                console.error(error);
            }
        };

    }

    function cropImage(minx, miny, maxx, maxy) {

        let xhr = new XMLHttpRequest();
        let data = new FormData();

        data.append('tny', map_size.y);
        data.append('tnx', map_size.x);
        data.append('minx', minx);
        data.append('miny', miny);
        data.append('maxx', maxx);
        data.append('maxy', maxy);

        xhr.open('POST', 'update_image_content');
        xhr.setRequestHeader("X-CSRFToken", token);
        xhr.send(data);

        xhr.onload = function(evt) {
            try {
                updateImageOverlay();

            } catch (error) {
                console.error(error);
            }
        };

    }

    function orthoImage() {
        ROUTE_ADDRESS = 'ortho_image';
        let output_image_path = document.getElementById('image_path_ortho');
        callRoute(ROUTE_ADDRESS, output_image_path.value)
    }

    function callRoute(routeName, value) {

        xhr = new XMLHttpRequest();
        data = new FormData();

        data.append('input', value);
        xhr.open('POST', routeName);
        xhr.setRequestHeader("X-CSRFToken", token);
        xhr.send(data)

    }