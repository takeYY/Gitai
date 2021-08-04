$(document).ready(function () {
  bsCustomFileInput.init()
  $('#inputFileReset').click(function () {
    let elem = document.getElementById('inputFile');
    elem.value = '';
    elem.dispatchEvent(new Event('change'));
  });
  document.getElementById('inputFile').disabled = false;
  document.getElementById('edogawa-works').disabled = false;
});

function countLength(field, text, max_length) {
  let text_length = text.length;
  let target = document.getElementById(field);
  if (text_length < 1) {
    target.setAttribute('class', 'text-right text-danger');
  } else if (0 < text_length && text_length < max_length*0.90) {
    target.setAttribute('class', 'text-right text-success');
  } else if (max_length * 0.90 <= text_length && text_length <= max_length) {
    target.setAttribute('class', 'text-right text-warning');
  }else {
    target.setAttribute('class', 'text-right text-danger');
  }
  target.innerHTML = `文字数：${Number(text_length).toLocaleString()}/${Number(max_length).toLocaleString()}`;
}
