// $(function(){
$(document).ready(function(){
	var $ = django.jQuery;
	// $("#id_eventinfo-event_mgmt").val(10).trigger('change');
	var events_info;
	var field_id_template = '#id_eventinfo-';
	var fields = ["event_mgmt","facility","salesperson","carrier","adv_wh","dir_wh"];
	

	function search_select2($ele, search_term){
		var result;
		var pattern = new RegExp('\\b('+search_term+')\\b', 'g');
		$ele.val("").trigger("change");
		$ele.find('option').each(function(){
			var match = this.innerText.match(pattern);
			if(match !== null && match.length >= 1){
				$ele.val(this.value).trigger("change");			
			}
		});
	}

	function create_booth_note(data){
		note = '';
		note += (data['BoothSize'] ? 'Booth Size ' + data['BoothSize'] + '\n' : '');
		note += (data['BoothColor'] ? 'BoothColor ' + data['BoothColor'] + '\n' : '');

		if(data['BoothTableSize']){			
			if((data['BoothBareTable'] && data['BoothBareTable'] == 'True')){
				note += 'Unskirted '
			}else if(data['BoothDrapedTable'] && data['BoothDrapedTable'] == 'True'){
				note += 'Skirted '
			}		
			note += data['BoothTableSize'] + ' Table \n';
		}
		// note += ( (data['BoothBareTable'] && data['BoothBareTable'] == 'True') ? 'Unskirted Table \n' : '');
		// note += ( (data['BoothDrapedTable'] && data['BoothDrapedTable'] == 'True') ? 'Skirted Table \n' : '');		
		// note += (data['BoothTableSize'] ? 'Table Size ' + data['BoothTableSize'] + '\n' : '');
		note += ( (data['BoothFoldingChairQty'] && data['BoothFoldingChairQty'] !== "0") ? 'Folding Chairs ' + data['BoothFoldingChairQty'] + '\n' : '');
		note += ( (data['BoothWasteBasket'] && data['BoothWasteBasket'] == 'True') ? 'Wastebasket' + '\n' : '');
		
		if(data['BoothSign'] == true){
			sign = 'Booth Sign '
			if(data['BoothNumber'] == true)	sign += 'with booth numbers';
			if(data['BoothLogo'] == true) sign += 'with company logo';
			note += sign + '\n';;
		}
		note += ((data['Booth8ftBackwall'] && data['Booth8ftBackwall'] == 'True') ? '8ft Backwall' + '\n' : '');
		note += ((data['Booth3ftSidewall'] && data['Booth3ftSidewall'] == 'True') ? '3ft Sidewall' + '\n' : '');
		console.log(note)
		return note;
	}	

	$("#id_eventinfo-event_name").on('change', function(e){	
		var $event_name = $(this);
		var event_info;
		$.ajax('/api/v1/event/'+$event_name.val()+'/').done(function(results){
			event_info = results;				
			search_select2($(field_id_template + 'event_mgmt'), event_info['EventMgmntPlaceCode'])
			search_select2($(field_id_template + 'facility'), event_info['EventPlaceCode'])
			// search_select2($(field_id_template + 'dir_wh'), event_info['EventPlaceCode'])
			search_select2($(field_id_template + 'salesperson'), event_info['SalespersonCode'])
			$("#id_eventinfo-booth_info").val(create_booth_note(event_info));
			$("#id_eventinfo-sales_tax").val(event_info['SalesTaxCode']);
		});
	});
});

