const React = React;
const ReactDOM = ReactDOM;


function paintFlag() {
    var width = (window.innerWidth);
    var height = 30;
    //$('#flag').attr('width', width);
    var c = document.getElementById("flag");
    var ctx = c.getContext("2d");
    ctx.beginPath();
    ctx.fillStyle = 'red';

    ctx.fillRect(0,0,width,height);
    ctx.fillRect(0,60,width,height);
    ctx.fillRect(0,120,width,height);
	ctx.fillRect(0,180,width,height);
}


function Header() { return(
	    <div id="title">
	    	<h1>Bowl of</h1><br /><h1>Pork</h1><span>*a blog</span>
			<br /><br /><br />
			<canvas id="flag"></canvas>
		</div>
		
	);
}

function Footer() { return(
		<i class="fa fa-copyright" aria-hidden="true"> Copyrighted to infinity and beyond</i>
	);
}

ReactDOM.render(<Header />, document.getElementById('rootHeader'));
ReactDOM.render(<Footer />, document.getElementById('rootFooter'));
paintFlag();