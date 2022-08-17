var latitude;
var longitude;


window.dash_clientside = Object.assign({}, window.dash_clientside, {

    clientside: {

        setCoords: function (latitude,longitude) {
          this.latitude = latitude;
          this.longitude = longitude;
        },

      }

});
