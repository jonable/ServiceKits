

// IE doesn't accept periods or dashes in the window name, but the element IDs
// we use to generate popup window names may contain them, therefore we map them
// to allowed characters in a reversible way so that we can locate the correct
// element when the popup window is dismissed.
function id_to_windowname(text) {
	text = text.replace(/\./g, '__dot__');
	text = text.replace(/\-/g, '__dash__');
	return text;
}

function windowname_to_id(text) {
    text = text.replace(/__dot__/g, '.');
    text = text.replace(/__dash__/g, '-');
    return text;
}

function open_child_window(href, name) {
	name = id_to_windowname(name);
	var win = window.open(href, name, 'height=500,width=800,resizable=yes,scrollbars=yes');
	win.focus();
	return win;
}
function trigger_new_window(e){
	console.log('click');
	var href = $(this).data('popup-href');
	var name = $(this).data('popup-name');
	var win = open_child_window(href, name);
}

function dismissRelatedLookupPopup(win, chosenId, itemRepr) {
	console.log('chosen id is ' + chosenId, 'name is: ', itemRepr);
	console.log(win.name);
	var field_name = windowname_to_id(win.name);
	$("[name=\""+field_name+"\"]").data('popup-chosenid', chosenId);
	$("#repr_"+field_name).val(itemRepr);
	$("[name=\""+field_name+"\"]").val(chosenId);
	win.close();
}
function dismissAddRelatedObjectPopup(win, chosenId, itemRepr) {
	console.log('new id is ' + chosenId, 'name is ' + itemRepr);	
	var field_name = windowname_to_id(win.name);
	$("[name=\""+field_name+"\"]").data('popup-chosenid', chosenId);
	$("#repr_"+field_name).val(itemRepr);
	$("[name=\""+field_name+"\"]").val(chosenId);
	win.close();	
}    	
function select_form_addmore(selector, type){	
	var newElement = $(selector).clone(true);
	var total = $('#id_' + type + '-TOTAL_FORMS').val();
	newElement.find(':input').each(function() {
		if(typeof $(this).attr('name') == 'undefined'){
			var $anchor = $(newElement.find('a.fb_show'));
			var name = $(this).attr('id').replace('-' + (total-1) + '-','-' + total + '-');
			var name = name.replace('repr_', '');
			var id = 'id_' + name;
			var repr_id = 'repr_' + name;
			$(this).attr({'id': repr_id}).val('').removeAttr('checked');	

			$anchor.data({
				"popup-name":name,
				"popup-id":id
			});
			$anchor.unbind('click', trigger_new_window);
			$anchor.click(trigger_new_window);
			return;
		}
		var name = $(this).attr('name').replace('-' + (total-1) + '-','-' + total + '-');
		var id = 'id_' + name;
		$(this).attr({'name': name, 'id': id}).val('').removeAttr('checked');
	});
	newElement.find('label').each(function() {
		var newFor = $(this).attr('for').replace('-' + (total-1) + '-','-' + total + '-');
		$(this).attr('for', newFor);
	});
	total++;
	$('#id_' + type + '-TOTAL_FORMS').val(total);
	$(selector).after(newElement);	
}


// $("#click").click(open_child_window)
// this will need to interact with the "add more" button too
$(document).ready(function(){
	// var $ = django.jQuery;
	$('[data-popup-name]').each(function(){
		var $anchor = $(this);
		// var $hidden_input = $($anchor.data('popup-id'));
		// var $text_input = $('[name="repr_'+$anchor.data('popup-name')+'"]')
		var href = $anchor.data('popup-href');
		var name = $anchor.data('popup-name');
		$anchor.click(trigger_new_window);
	});
	// $('.close-icon').on('click', function(){
	// 	$(this).parent('.search-wrapper').find('input').each(function(){
	// 		$(this).val('');
	// 	});
	// });
});


