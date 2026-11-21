'use strict';
const { dumpsWorkbook } = require('./writer');
const { fromJson } = require('./model');

module.exports = { dumpsWorkbook, fromJson, loadXlsx: (...a) => require('./xlsx').loadXlsx(...a) };
