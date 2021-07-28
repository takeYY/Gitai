$(document).ready(function () {
  bsCustomFileInput.init()
  $('#inputFileReset').click(function () {
    let elem = document.getElementById('inputFile');
    elem.value = '';
    elem.dispatchEvent(new Event('change'));
  });
  document.getElementById('inputFile').disabled = false;
  document.getElementById('edogawa-works').disabled = false;
})
