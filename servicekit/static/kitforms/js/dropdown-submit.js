django.jQuery(function(){
	document.getElementById('id_status').onfocus = function (){this.previous_value = this.value;}
	document.getElementById('id_status').onchange = function (){	
		document.getElementById('id_notify').value = confirm('Send status update?');		
		this.form.submit();
	}
})