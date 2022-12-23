// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyAAvBW0AJEAIhfo5_w8Go8qnzXYwy1S3XY",
  authDomain: "smart-pet-monitor-a9aaf.firebaseapp.com",
  databaseURL: "https://smart-pet-monitor-a9aaf-default-rtdb.europe-west1.firebasedatabase.app",
  projectId: "smart-pet-monitor-a9aaf",
  storageBucket: "smart-pet-monitor-a9aaf.appspot.com",
  messagingSenderId: "825508932657",
  appId: "1:825508932657:web:cd7700d8928043b5137910"
};

firebase.initializeApp(firebaseConfig);

// Get a reference to the file storage service
const storage = firebase.storage();
// Get a reference to the database service
const database = firebase.database();

// Create camera database reference
const camRef = database.ref("file");

// Sync on any updates to the DB. THIS CODE RUNS EVERY TIME AN UPDATE OCCURS ON THE DB.
camRef.limitToLast(1).on("value", function(snapshot) {
  snapshot.forEach(function(childSnapshot) {
    const image = childSnapshot.val()["image"];
    const time = childSnapshot.val()["timestamp"];
    const storageRef = storage.ref(image);

    storageRef
      .getDownloadURL()
      .then(function(url) {
        console.log(url);
        document.getElementById("photo").src = url;
        document.getElementById("time").innerText = time;
        sendEmail(url,"http://192.168.8.116:8000/stream.mjpg",time);
      })
      .catch(function(error) {
        console.log(error);
      });
  });
});


function sendEmail(url,url2,time) {
     
  emailjs.send("service_ucvo77n","template_n6atl1t",{
  time: time,
  url: url,
  url2: url2  
  },"QB8DxBxQFHVazdYlg");
  
}