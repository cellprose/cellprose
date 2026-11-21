// What the site's browser bundle exports: the JS writer (js/src) and the viewer's parser (viewer/core).
const { loadXlsx, dumpsWorkbook, fromJson } = require('../../js/src');
const core = require('../../viewer/core/cellprose-core.js');
module.exports = { loadXlsx, dumpsWorkbook, fromJson, core };
