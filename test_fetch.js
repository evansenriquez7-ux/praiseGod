const fetch = require('node-fetch');
fetch('http://127.0.0.1:8081/__/functions.yaml')
  .then(res => res.text())
  .then(text => console.log('SUCCESS'))
  .catch(err => console.error('ERROR', err));
