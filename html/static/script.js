function checkboxChange(element, uid, pwg, add) {
  let data = {"uid": uid, "pwg": pwg, "checked": add ? 1 : 0};
  $.ajax({
    type: "POST",
    contentType: "application/json",
    url: "update",
    data: JSON.stringify(data),
  }).done(function (data) {
    if (!add) {
      $(element).parent().remove();
    } else {
      let newPwg = '<li>';
      newPwg += '<span title="' + pwg + ' is interested in this sample">' + pwg + '</span>\n';
      newPwg += '<button type="button" class="badge badge-pill badge-danger" title="Remove ' + pwg + ' from interested PWGs" onclick="checkboxChange(this, \'' + uid + '\', \'' + pwg + '\', false)">X</button>';
      newPwg += '</li>';
      $(element).parent().before(newPwg);
      element.value = '';
    }
  }).fail(function(data) {
    alert('Error');
  })
}
