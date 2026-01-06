
const myHeaders = new Headers();
myHeaders.append("Accept", "application/json");

$('#apply-filter-fields').on('click', async function() {
  var fieldsCount = $('#filter-fields-count').val();
  var filters = []
  for (i = 0; i < fieldsCount; i++) { 
    console.log(i);
    field = {
      id:   $(`#filter-field-name-${i}`).val(),
      label: $(`#filter-field-name-${i}`).val(),
      type: $(`#filter-field-type-${i}`).val()
    }
    filters.push(field);
  }
  await setFilters(filters);

});

async function setFilters(filters){
  var isEmpty = $("#builder-basic").html() === "";
  if (isEmpty){

    $('#builder-basic').queryBuilder({
      plugins: ['bt-tooltip-errors'],
  
      filters: filters,
  
    });
    document.getElementById('builder-btn-group').classList.remove("hidden");

  }else{
    $('#builder-basic').queryBuilder('reset');
    $('#builder-basic').queryBuilder('setFilters', true, filters);

  }
}


async function addField(){
  var fieldsCount = $('#filter-fields-count');
  fields = $('#filter-fields');
  cloneFieldElements = $('#filter-field').clone(true).find("*[id]").addBack().each(
    function() { 
      $(this).attr("id", $(this).attr("id") + `-${Number(fieldsCount.val())}`); 
    }
  );
  cloneFieldElements[0].classList.remove("hidden");
  result = cloneFieldElements[0];
  result.append(...cloneFieldElements.slice(1));
  fields.append(result);
  fieldsCount.val(Number(fieldsCount.val())+1);
}

function changeIdField(field, id){
  field.find("*[id]").addBack().each(
    function() { 
      $(this).attr("id", $(this).attr("id").split("-").slice(0, -1).join("-") + `-${id}`); 
    }
  );
}

// Функция для отправки запросов
const sendRequest = async (url, data) => {
    try {
        const authRequestOptions = {
          method: "POST",
          headers: myHeaders,
          body: data,
        };
        const response = await fetch(url, authRequestOptions);
        console.log(response);
        const result = await response.json();
        if (response.ok) {
            alert(result.message || 'Операция выполнена успешно!');
            return result;
        } else {
            alert(result.message || 'Ошибка выполнения запроса!');
            return null;
        }
    } catch (error) {
        console.error("Ошибка:", error);
        alert('Произошла ошибка на сервере');
    }
};

$('#btn-reset').on('click', function() {
  $('#builder-basic').queryBuilder('reset');
});


$('.delete-filter-field').on('click', async function() {
  deletedField = $(this).parent();
  var fieldsCount = $('#filter-fields-count');
  for (i = Number(deletedField.attr('id').replace("filter-field-", "")); i < fieldsCount.val(); i++) { 
    await changeIdField($(`#filter-field-${i+1}`), i);
  }
  $(this).parent().remove();
  fieldsCount.val(Number(fieldsCount.val())-1);

});


$('.btn-create-connections').on('click', async function() {
  connectionContainer = $("#connection-0");
  searchType = $(connectionContainer).find("[name=search_type]").val();
  request = {
    "name": $(connectionContainer).find("[name=name]").val(),
    "params": $(connectionContainer).find("[name=params]").val(),
    "request_url": $(connectionContainer).find("[name=request_url]").val(),
    "method": $(connectionContainer).find("[name=select-type-method]").val(),
    "headers": $(connectionContainer).find("[name=headers]").val(),
    "url_params": $(connectionContainer).find("[name=url_params]").val(),
  }
  var rules = $('#builder-basic').queryBuilder('getRules');
  var filters = $('#builder-basic').queryBuilder('getFilters');
//
//  if (!$.isEmptyObject(rules)) {
//    JSON.stringify(rules, null, 2);
//  }
  connection = {
    "search_type": searchType,
    "step_id": "ccd10449-d110-4168-9577-74419b37ca06",
    "next_step_id": "c323ec8b-12a7-4f1b-a8dc-0538a64ad916",
    "rules": rules,
    "plugins": null,
    "filters": filters,
    "request": request
  }
  await sendRequest("api/v1/connection/", connection);
});


$('#btn-add-filter-field').on('click', async function() {
  await addField();
});

// $('#btn-set').on('click', function() {
//   $('#builder-basic').queryBuilder('setRules', rules_basic);
// });

$('#btn-get').on('click', function() {
  var result = $('#builder-basic').queryBuilder('getRules');

  if (!$.isEmptyObject(result)) {
    console.log(JSON.stringify(result, null, 2));
  }
});

$('#btn-get-filters').on('click', function() {
  var result = $('#builder-basic').queryBuilder('getFilters');

  if (!$.isEmptyObject(result)) {
    console.log(JSON.stringify(result, null, 2));
  }
});

// $('#builder-basic').queryBuilder({
//   plugins: ['bt-tooltip-errors'],

//   filters: [{
//     id: 'name',
//     label: 'Name',
//     type: 'string'
//   }, {
//     id: 'category',
//     label: 'Category',
//     type: 'integer',
//     input: 'select',
//     values: {
//       1: 'Books',
//       2: 'Movies',
//       3: 'Music',
//       4: 'Tools',
//       5: 'Goodies',
//       6: 'Clothes'
//     },
//     operators: ['equal', 'not_equal', 'in', 'not_in', 'is_null', 'is_not_null']
//   }, {
//     id: 'in_stock',
//     label: 'In stock',
//     type: 'integer',
//     input: 'radio',
//     values: {
//       1: 'Yes',
//       0: 'No'
//     },
//     operators: ['equal']
//   }, {
//     id: 'price',
//     label: 'Price',
//     type: 'double',
//     validation: {
//       min: 0,
//       step: 0.01
//     }
//   }, {
//     id: 'id',
//     label: 'Identifier',
//     type: 'string',
//     placeholder: '____-____-____',
//     operators: ['equal', 'not_equal'],
//     validation: {
//       format: /^.{4}-.{4}-.{4}$/
//     }
//   }],

//   rules: rules
// });