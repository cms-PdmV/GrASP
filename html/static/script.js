function changeInterestedPWG(element, uid, pwg, add) {
  let data = {"uid": uid, "pwg": pwg, "checked": add ? 1 : 0};
  $.ajax({
    type: "POST",
    contentType: "application/json",
    url: "update",
    data: JSON.stringify(data),
  }).done(function (data) {
    if (!add) {
      $(element).parent().remove();
      selectPWG(undefined, pwg);
    } else {
      let newPwg = '<li>'
      newPwg += '<span title="' + pwg + ' is interested in this sample">' + pwg + '</span>&nbsp;'
      newPwg += '<a class="group group-remove group-remove-'+pwg+'" '
      newPwg += 'title="Remove ' + pwg+ ' from interested PWGs" '
      newPwg += 'onclick="changeInterestedPWG(this, \'' + uid + '\', \'' + pwg + '\', false)">Remove</a>'
      newPwg += '</li>'
      $(element).parent().parent().parent().find('ul.interested-list').first().append(newPwg);
      $(element).parent().hide();
    }
  }).fail(function(data) {
    alert('Error: ' + data.responseText);
  })
}

function selectPWG(element, pwg) {
  $('.group').hide();
  $('.group-remove-' + pwg).show();
  $.each($('ul.interested-list'), function(index, el) {
    if ($(el).find('.group-remove-' + pwg).length === 0) {
      $(el).parent().find('.group-add-' + pwg).show();
    }
  });
}

function clearNotes(element, uid) {
  $(element).parent().find('textarea').get(0).value = '';
  let data = {"uid": uid, "notes": ''};
  $.ajax({
    type: "POST",
    contentType: "application/json",
    url: "update",
    data: JSON.stringify(data),
  }).done(function (data) {
    alert('Text reset in the database');
  }).fail(function(data) {
    alert('Not reset');
  })
}

function saveNotes(element, uid) {
    // Take the value of the text box
    let notes = $(element).parent().find('textarea').get(0).value;
    console.log(notes);
    console.log($(element).parent().find('textarea').get(0));
    let data = {"uid": uid, "notes": notes};
    $.ajax({
        type: "POST",
        contentType: "application/json",
        url: "update",
        data: JSON.stringify(data),
    }).done(function (data) {
        alert('Text saved in the database');
    }).fail(function(data) {
        alert('Error in saving');
    })    
}
