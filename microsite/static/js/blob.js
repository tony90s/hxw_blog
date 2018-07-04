function getBlobBydataURI(dataURI, type) {
    var binary = atob(dataURI);
    var array = [];
    for (var i = 0; i < binary.length; i++) {
        array.push(binary.charCodeAt(i));
    }
    return new Blob([new Uint8Array(array)], {type: type});
}
