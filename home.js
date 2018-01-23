const React = React;
const ReactDOM = ReactDOM;
var filestor = firebase.storage();
const posts = new Array();

function getPosts() {
	var pref = filestor.ref('posts/');
	var dbRef = firebase.database().ref('/postData');
	dbRef.once('value', (snapshot) => {
		snapshot.forEach((item) => {
			pref.child(item.key+'.html').getDownloadURL().then((url) => {
				$.get(url, (data) => { 
					posts.push({"name": item.val().name, "sk": item.key, "title":item.val().title, "loves": item.val().loves,  "date":item.val().date});
					populate();
					$('[postId|="'+item.key+'"]').first().append(data.substring(0, 400)+"<p> ...</p>");
					$('.fa-heart-o').click(function() {
						$(this).attr('class', 'fa fa-heart');
						dbRef.child($(this).attr('id')).update({loves: (parseInt($(this).attr('num'), 10)+1)});
						$(this).empty().append(' '+(parseInt($(this).attr('num'), 10)+1)+' loves');
					});
					$('.fa-spin').hide();
				});
			});
		});
	});
}
getPosts();


function Post(p) { return(
    <div id="post">
        <h1>{ p.title }</h1>
        <div id="content" postId={ p.sk }></div>
        <a href={ "/post.html?id="+p.sk }><button><span>Take me there</span></button></a><i className="fa fa-heart-o" id={p.sk} num={ p.loves }> { p.loves } loves</i><i className="fa">{ p.date }</i>
    </div>
    );
}


function Expose() { return(
    	<div>{posts.map((item) => <Post title={item.title} sk={item.sk} loves={item.loves} date={item.date} href={item.name} />)}</div>
	);
}


function populate() {
	ReactDOM.render(<Expose />, document.getElementById('root'));
}
