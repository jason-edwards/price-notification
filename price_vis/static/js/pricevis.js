function DataAdaptor(url) {
	this.url = url;

	this.getPricelog = function(asxCode, callback, startDate, endDate) {
		startDate = startDate instanceof Date ? startDate : null;
		endDate = endDate instanceof Date ? endDate : null;

		requestData = { 
			asx_code: asxCode,
			start_date: new Date(2014),
			max_count: 100
		}
		
		$.ajax({
			method: "POST",
			url: this.url,
			contentType: "application/json",
			dataType: "json",
			data: JSON.stringify(requestData)
		})
		.done(function(reply) {
			var processedValues = [];
			var parsedDate;
			for (var i = 0; i < reply.values.length; i++) {
				parsedDate = new Date(reply.values[i][0]);
				processedValues.push({x: parsedDate, y: reply.values[i][1]});
			}
			callback(processedValues);
		});
	}
}


$(function() {
	var dataAdaptor = new DataAdaptor('http://localhost:8000/json/');

	var data = [{
		key: "price",
		color: "orange",
		values: []
	}];

	var chart;

	nv.addGraph(function() {
	    chart = nv.models.lineChart()
	                    .showYAxis(true)
	                    .showXAxis(true);

	    chart.xAxis
	        .axisLabel('Date')
	        .tickFormat(d3.format(',r'));

	    chart.yAxis
	        .axisLabel('Price')
	        .tickFormat(d3.format('.02f'));

	    d3.select('#chart svg')
		        .datum(data)
		        .call(chart);

		// This is spamming all the time for some reason
	    //nv.utils.windowResize(function() { chart.update() }); 
	    return chart;
	});

	var timeout;
	function updateChart() {
		dataAdaptor.getPricelog(
			'cba',
			function(values) {
				data[0].values = values;
				chart.update();
				timeout = setTimeout(updateChart, 2000);
			},
			Date(2015),
			Date(2016));
	}

	timeout = setTimeout(updateChart, 2000);
});