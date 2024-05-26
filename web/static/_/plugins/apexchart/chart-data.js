'use strict';

$(document).ready(function() {

	function generateData(baseval, count, yrange) {
		var i = 0;
		var series = [];
		while (i < count) {
			var x = Math.floor(Math.random() * (750 - 1 + 1)) + 1;;
			var y = Math.floor(Math.random() * (yrange.max - yrange.min + 1)) + yrange.min;
			var z = Math.floor(Math.random() * (75 - 15 + 1)) + 15;

			series.push([x, y, z]);
			baseval += 86400000;
			i++;
		}
		return series;
	}
	
	// Simple Column
	
	if ($('#performance-user').length > 0) {
		var sCol = {
			chart: {
				height: 280,
				type: 'bar',
				toolbar: {
				  show: false,
				}
			},
			plotOptions: {
				bar: {
					horizontal: false,
					columnWidth: '20%',
					endingShape: 'rounded'  
				},
			},
			// colors: ['#888ea8', '#4361ee'],
			dataLabels: {
				enabled: false
			},
			stroke: {
				show: true,
				width: 2,
				colors: ['transparent']
			},
			series: [{
				name: "High",
				color: '#4F46E5',
				data: [70, 85, 101, 90]
			}, {
				name: "Low",
				color: '#CBD4E0',
				data: [50, 40, 50, 20]
			}],
			fill: {
				opacity: 1

			},
			tooltip: {
				y: {
					formatter: function (val) {
						return "$ " + val + " thousands"
					}
				}
			},
			xaxis: {
			categories: ['1', '2', '3', '4', '5'],
			}
		}

		var chart = new ApexCharts(
			document.querySelector("#performance-user"),
			sCol
		);

		chart.render();
	}
  
});