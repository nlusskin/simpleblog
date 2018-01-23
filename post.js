const React = React;
const ReactDOM = ReactDOM;
var filestor = firebase.storage();
var id = window.location.search.split('id=')[1];
var posts = new Array();

function getPost() {
	var pref = filestor.ref('posts/');
	var dbRef = firebase.database().ref('postData/'+decodeURIComponent(id));
	dbRef.once('value', (snapshot) => {
		var item = snapshot.val();
			pref.child(snapshot.key+'.html').getDownloadURL().then((url) => {
				$.get(url, (data) => { 
					posts.push({"name": item.name, "title":item.title, "loves": item.loves,  "date":item.date});
					populate();
					$('#content').first().append(data);
					$('.fa-heart-o').click(function() {
						$(this).attr('class', 'fa fa-heart');
						dbRef.update({loves: (parseInt($(this).attr('num'), 10)+1)});
						$(this).empty().append(' '+(parseInt($(this).attr('num'), 10)+1)+' loves');
					});
					$('.fa-spin').hide();
				});
			});
		});
}
getPost();



function Post(p) { return(
    <div id="post">
        <h1>{ p.title }</h1><br></br><br></br>
        <i className="fa fa-heart-o" id={p.title} num={ p.loves }> { p.loves } loves</i><i className="fa">{ p.date }</i>
        <div id="content"></div>
    </div>
    );
}


function Expose() { return(
    	<div>{posts.map((item) => <Post title={item.title} loves={item.loves} date={item.date} href={item.name} />)}</div>
	);
}


function populate() {
	ReactDOM.render(<Expose />, document.getElementById('root'));
}
