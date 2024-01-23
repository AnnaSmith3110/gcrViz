//happened as student is accessing teacher scope. can be rectified by checking scope of user first and redirecting accordingly
//FIEXD:NOT AUTHORIZED AS THERE IS LIKELY SOME ERROR WITH ACCESS TOKEN ie: req.user.accessToken
app.get('/success', (req, res) => {
  //ERROR HANDLING
  console.log("CHECK ACCESS TOKEN",req.user.accessToken)
  if (req.isAuthenticated() && req.user.accessToken) {
    console.log("in success fn")
    //set user access token for API client
    oauth2Client.setCredentials({ access_token: req.user.accessToken });
    console.log("Access token:", req.user.accessToken);
    console.log("after obtaining access token")
    //create classroom API client 
    const classroom = google.classroom({ version: 'v1', auth: oauth2Client });
    console.log("built classroom")

    //EXAMPLE: LIST OF COURSES
    classroom.courses.list({}, (err, response) => {
      console.log("in courses.list")
      if (err) {
        console.error('Error listing courses', err);
        res.status(500).send('Error listing courses');
        return;
      }
      const courses = response.data.courses;
      console.log("after error, getting courses")

      //EXAMPLE: COURSEWORK FOR STUDENT
      const courseWorkPromises = courses.map((course) => {
        return new Promise((resolve, reject) => {
          classroom.courses.courseWork.list({courseId:course.id}, (err, courseWorkResponse) => {
            if(err) {
              console.error("Error listing coursework", err);
              reject(err);
            }
            else {
              course.courseWork = courseWorkResponse.data.courseWork;
              resolve(course);
            }
          });
        });
      });
      //wait for all coursework requests to complete 
      Promise.all(courseWorkPromises)
      .then((coursesWithCoursework) => {
        console.log("after fetching courses");
        //access user data using req.user
        res.send('Welcome '+req.user.profile.displayName+'<br>Courses and Course Work'+JSON.stringify(coursesWithCoursework));
        console.log("after welcome");
      })
      .catch((err) => {
        console.error("Error listing course wth coursework");
        res.status(500).send("Error listing course wth coursework");
      });
      // // You can access user data using req.user
      // res.send('Welcome, ' + req.user.profile.displayName + '<br>Courses: ' + JSON.stringify(courses));
      // console.log("after welcome")
    });
  }
  else {
    res.send("You are not authenticated")
  }
});