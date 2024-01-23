const express = require('express');
const passport = require('passport');
const GoogleStrategy = require('passport-google-oauth20').Strategy;
const session = require('express-session');
const dotenv = require('dotenv'); // Import the dotenv library
const { google } = require('googleapis');

const classroomScopes = [
  //ONLY FOR TEACHERS
  'https://www.googleapis.com/auth/classroom.coursework.students', 
  "https://www.googleapis.com/auth/classroom.coursework.students.readonly",

  //ONLY FOR STUDENTS
  'https://www.googleapis.com/auth/classroom.courses', // Access to courses a student is enrolled in.
  "https://www.googleapis.com/auth/classroom.coursework.me",
  "https://www.googleapis.com/auth/classroom.coursework.me.readonly",
  'https://www.googleapis.com/auth/classroom.rosters.readonly', // Access to course rosters, including info about teachers and classmates.
  'https://www.googleapis.com/auth/classroom.profile.emails', // Access to the student's email address associated with their Google account.
  'https://www.googleapis.com/auth/classroom.profile.photos', // Access to the student's profile photo.
  'https://www.googleapis.com/auth/classroom.student-submissions.me.readonly', 
  'https://www.googleapis.com/auth/classroom.coursework.me.readonly', //Access to own submissions
  'https://www.googleapis.com/auth/classroom.guardianlinks.students', // Access to guardian links associated with the student's account.
  'https://www.googleapis.com/auth/drive', //acccess submission in drive?
  'https://www.googleapis.com/auth/documents' //same as above
  // Add more scopes as needed
];

// Initialize Google API Client function
function initializeGoogleApiClient() {
  const oauth2Client = new google.auth.OAuth2(
    process.env.GOOGLE_CLIENT_ID,
    process.env.GOOGLE_CLIENT_SECRET,
    process.env.GOOGLE_REDIRECT_URI
  );
  // Set the desired scopes
  oauth2Client.setCredentials({ scope: classroomScopes });

  return oauth2Client;
}
// Initialize the Google API client
const oauth2Client = initializeGoogleApiClient();

dotenv.config();
const app = express();
const path = require('path');
const { rejects } = require('assert');

// Use sessions to keep track of user's login state
app.use(session({ secret: 'secret', resave: false, saveUninitialized: true }));

// Initialize Passport
app.use(passport.initialize());
app.use(passport.session());

// Set the 'views' directory for your EJS templates
app.set('views', path.join(__dirname, 'views'));
//use ejs
app.set('view engine', 'ejs');

// Set up the Google OAuth 2.0 strategy
passport.use(new GoogleStrategy({
  clientID: process.env.GOOGLE_CLIENT_ID, // Use environment variables
  clientSecret: process.env.GOOGLE_CLIENT_SECRET,
  callbackURL: process.env.GOOGLE_REDIRECT_URI,
},
  function (accessToken, refreshToken, profile, done) {
    // This function is called after successful authentication
    // You can save user data in your database here or perform other actions

    return done(null, { profile, accessToken, refreshToken });
  }));

// Serialize and deserialize user data
passport.serializeUser(function (user, done) {
  //Including user role to display authorized data.eg: student scope can access only student functions
  const serializedUser = {...user, role:user.profile.role}; //DOES NOT WORK AS NO ROLE IS SPECIFIED IN THE GCR API
  done(null, serializedUser);
  console.log("SCOPE OF USER",serializedUser);
});

passport.deserializeUser(function (obj, done) {
  done(null, obj);
});

app.get('/', (req, res) => {
  // This function will be executed when a GET request to the root path ("/") is made
  res.sendFile(path.join(__dirname + '/pages/index.html'));

});

// Define routes for authentication
app.get('/auth/google',
  passport.authenticate('google', {
    scope: [
      'profile', 
      'email', 
      //teachers
      'https://www.googleapis.com/auth/classroom.coursework.students',
      'https://www.googleapis.com/auth/classroom.coursework.students',
      //students
      'https://www.googleapis.com/auth/classroom.courses', 
      'https://www.googleapis.com/auth/classroom.student-submissions.me.readonly', //own submissions+grades
      'https://www.googleapis.com/auth/classroom.rosters.readonly',
      'https://www.googleapis.com/auth/classroom.profile.emails',
      'https://www.googleapis.com/auth/classroom.profile.photos',
      'https://www.googleapis.com/auth/classroom.guardianlinks.students',
      'https://www.googleapis.com/auth/drive', //acccess submission in drive?
      'https://www.googleapis.com/auth/documents'
      ],
    })
);

app.get('/callback',
  passport.authenticate('google', { failureRedirect: '/' }),
  function (req, res) {
    // Successful authentication, redirect to a success page or return user data
    console.log("BEFORE REDIRECTING TO SUCCESS PRINT PROFILE", req.user.profile);
    res.redirect('/success');
  }
);

//FIEXD:NOT AUTHORIZED AS THERE IS LIKELY SOME ERROR WITH ACCESS TOKEN ie: req.user.accessToken
app.get('/success', (req, res) => {
  // //ERROR HANDLING
  // console.log("CHECK ACCESS TOKEN",req.user.accessToken)
  if (req.isAuthenticated() && req.user.accessToken) {
    console.log("in success fn")
    //set user access token for API client
    oauth2Client.setCredentials({ access_token: req.user.accessToken });
    console.log("Access token:", req.user.accessToken);
    console.log("after obtaining access token")
  
    res.render("selectRole", {user:req.user});
    // res.status(200).send('Welcome ' + req.user.profile.displayName);
  }
  else {
    res.send("You are not authenticated")
  }
});

app.get('/teacher', (req, res) => {
  if (req.isAuthenticated() && req.user.accessToken) {
    const classroom = google.classroom({ version: 'v1', auth: oauth2Client });

    // 1. GET LIST OF ENROLLED COURSES
    classroom.courses.list({}, (err, response) => {
      if (err) {
        console.error('Error listing student courses', err);
        res.status(500).send('Error listing student courses');
        return;
      }
      const courses = response.data.courses;

      // 2. GET LIST OF STUDENT SUBMISSIONS
      // Iterate over each course and extract the course's submissions
      const submissionsPromises = courses.map(course => {
        return new Promise((resolve, reject) => {
          classroom.courses.courseWork.list({ courseId: course.id }, (err, courseWorkResponse) => {
            if (err) {
              console.error("Error listing student submissions for course Id: ", err);
              reject(err);
            } else {
              const courseWorkList = courseWorkResponse.data.courseWork;

              //throws error if nothing is submitted, so to overcome it:
              if(!Array.isArray(courseWorkList)) {
                console.error("CourseWorkList is not an array for course Id: ", course.id);
                reject("Invalid courseWorkList");
                return;
              }

              // Fetch student submissions for each coursework
              const submissionsPromises = courseWorkList.map(courseWork => {
                return new Promise((resolveCourseWork, rejectCourseWork) => {
                  classroom.courses.courseWork.studentSubmissions.list({
                    courseId: course.id,
                    courseWorkId: courseWork.id
                  }, (err, submissionsResponse) => {
                    if (err) {
                      console.error("Error listing student submissions for course Id:", course.id, "CourseWorkId:", courseWork.id, "Error:", err);
                      rejectCourseWork(err);
                    } else {
                      const studentSubmissions = submissionsResponse.data.studentSubmissions;
                      resolveCourseWork({
                        courseWorkId: courseWork.id,
                        submissions: studentSubmissions
                      });
                    }
                  });
                });
              });

              // Wait for all coursework submissions to be fetched
              Promise.all(submissionsPromises)
                .then(courseWorkSubmissions => {
                  course.courseWorkSubmissions = courseWorkSubmissions;
                  resolve(course);
                })
                .catch(reject);
            }
          });
        });
      });

      // Wait for all courses and their submissions to be fetched
      Promise.all(submissionsPromises)
        .then(coursesWithSubmissions => {
          // Render user details + course info
          res.render("teacher", { user: req.user, courses: coursesWithSubmissions });
        })
        .catch(err => {
          console.error("Error fetching student submissions:", err);
          res.status(500).send('Error fetching student submissions');
        });
    });
  } else {
    res.send("You are not authenticated");
  }
});

app.get('/student', (req, res) => {
  if (req.isAuthenticated() && req.user.accessToken) {
    const classroom = google.classroom({ version: 'v1', auth: oauth2Client });

    // 1. GET LIST OF ENROLLED COURSES
    classroom.courses.list({}, (err, response) => {
      if (err) {
        console.error('Error listing student courses', err);
        res.status(500).send('Error listing student courses');
        return;
      }
      const courses = response.data.courses;
      console.log("COURSE DETS: ", courses);

      // 2. GET LIST OF STUDENT SUBMISSIONS
      const studentId = req.user.profile.id;
      console.log("STUDENT ID: ", studentId);

      // Create submissions promises
      const submissionsPromises = [];
      // Fetching student submissions for each course using FOREACH
      courses.forEach(course => {
        classroom.courses.courseWork.studentSubmissions.list( //28TH: CHANGED THE API CALL
          { courseId: course.id }, (err, courseWorkResponse) => {
            if (err) {
              console.error("Error listing coursework for course Id: ", course.id, "Error: ", err);
            } else {
              const courseWorkList = courseWorkResponse.data.courseWork;
              // Fetching student submission by iterating over each course item
              courseWorkList.forEach(courseWork => {
                // Push promise to array of promises
                submissionsPromises.push(new Promise((resolve, reject) => {
                  classroom.courses.courseWork.studentSubmissions.get({
                    courseId: course.id,
                    courseWorkId: courseWork.id,
                    id: studentId // GET FOR PARTICULAR STUDENT
                  }, (err, submissionResponse) => {
                    if (err) {
                      console.error("Error fetching students submission for course id: ", course.id, " course work id: ", courseWork.id, " Error: ", err);
                      reject(err);
                    } else {
                      const studentSubmission = submissionResponse.data;
                      resolve({
                        courseName: course.name, 
                        courseWorkTitle: courseWork.title,
                        submission: studentSubmission
                      });
                    }
                  });
                }));
              });
            }
          });
      });

      // Resolve promises
      Promise.all(submissionsPromises)
        .then(studentSubmissions => {
          res.render("student", { user: req.user, courses: courses, submissions: studentSubmissions });
        })
        .catch(err => {
          console.error("Error fetching student submissions:", err);
          res.status(500).send('Error fetching student submissions');
        });
    });
  } else {
    res.send("You are not authenticated");
  }
});



app.listen(5000, () => {
  console.log('Server started on http://localhost:5000');
});
