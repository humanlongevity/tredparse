const Converter = require("csvtojson").Converter;
const fs = require("fs");
const path = require("path");

// CSV File Path or CSV String or Readable Stream Object
const csvFileName = path.join(__dirname, "../../../tredparse/data/TREDs.meta.hg38.csv");

//new converter instance
const csvConverter = new Converter({});

var Meta = "";
// end_parsed will be emitted once parsing finished
csvConverter.on("end_parsed", (jsonObj) => {
    console.log(jsonObj); //here is your result json object
    Meta = jsonObj;
});

//read from file
fs.createReadStream(csvFileName).pipe(csvConverter);
module.exports = Meta;
