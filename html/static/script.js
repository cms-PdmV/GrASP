function changeInterestedPWG(element, uid, pwg, add) {
  let data = {"uid": uid, "pwg": pwg, "checked": add ? 1 : 0};
  $.ajax({
    type: "POST",
    contentType: "application/json",
    url: "/samples/update",
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
    url: "/samples/update",
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
    url: "/samples/update",
    data: JSON.stringify(data),
  }).done(function (data) {
    alert('Text saved in the database');
  }).fail(function(data) {
    alert('Error in saving');
  })
}

function clearNotesMissing(element, dataset_name, campaign) {
  $(element).parent().find('textarea').get(0).value = '';
  let data = {"dataset_name": dataset_name, "campaign": campaign, "missing_nts": ''};
  saveNotesMissing(element, dataset_name, campaign);
}

function saveNotesMissing(element, dataset_name, campaign) {
  // Take the value of the text box
  let notes = $(element).parent().find('textarea').get(0).value;
  console.log(notes);
  console.log($(element).parent().find('textarea').get(0));
  let data = {"dataset_name": dataset_name, "campaign": campaign, "missing_nts": ''};
  $.ajax({
    type: "POST",
    contentType: "application/json",
    url: "/samples/missing_update",
    data: JSON.stringify(data),
  }).done(function (data) {
    alert('Text saved in the database');
  }).fail(function(data) {
    alert('Error in saving: '+ data.responseText);
  })
}

$(document).ready(function() {
  let domain = document.location.origin;
  if (domain && domain.includes('dev')) {
    $('body').addClass('dev-ribbon');
  }
  $("#missingSampleTable").DataTable({
                                      "processing": true,
                                      "pageLength": 20,
                                      dom: 'Bfrtip',
                                      buttons: [
                                        'copy', 'csv', 'excel', 'pdf', 'print'
                                      ]
                                  });
  $('.dataTables_length').addClass('bs-select');

});

function addSample(element) {
    console.log($(element).parent().parent().parent());
    let datasetname = $(element).parent().parent().parent().find('#datasetnamerun3').get(0).value;
    console.log(datasetname);
    let numberevents = $(element).parent().parent().parent().find('#numberofevents').get(0).value;
    console.log(numberevents);
    let interested_pwgs = $(element).parent().parent().parent().find('#pwginterested').get(0).value;
    console.log(interested_pwgs);
    let data = {"datasetname": datasetname, "numberofevents": numberevents, "pwginterested": interested_pwgs};
    $.ajax({
      type: "POST",
      contentType: "application/json",
      url: "/samples/add_run3",
      data: JSON.stringify(data),
    }).done(function (data) {
      alert('Text saved in the database');
      window.location.reload(true);
    }).fail(function(data) {
      alert('Error in saving the dictionary: ' + data.responseText);
    })
}

function removeSample(element, uid) {
    let data = {"uid": uid};
    $.ajax({
      type: "POST",
      contentType: "application/json",
      url: "/samples/remove_run3",
      data: JSON.stringify(data),
    }).done(function (data) {
      alert('Text removed from the database');
      window.location.reload(true);
    }).fail(function(data) {
      alert('Error in removing from the dictionary: ' + data.responseText);
    })
}

function updateSample(element, uid) {
    let interested_pwgs = $(element).parent().parent().parent().find('#pwginterested').get(0).value;
    console.log(interested_pwgs);
    let data = {"uid": uid, "pwginterested": interested_pwgs};
    $.ajax({
      type: "POST",
      contentType: "application/json",
      url: "/samples/update_run3",
      data: JSON.stringify(data),
    }).done(function (data) {
      alert('Text removed from the database');
      window.location.reload(true);
    }).fail(function(data) {
      alert('Error in removing from the dictionary: ' + data.responseText);
    })
}
