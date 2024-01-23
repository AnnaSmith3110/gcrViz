const express = require('express');
const passport = require('passport');
const GoogleStrategy = require('passport-google-oauth20').Strategy;
const session = require('express-session');
const dotenv = require('dotenv'); // Import the dotenv library
const { google } = require('googleapis');
const axios = require('axios')
const bodyParser = require('body-parser'); // Import bodyParser
const { spawn } = require('child_process');
const fs = require('fs'); //write into file
const classroomScopes = [
  //BOTH 
  'https://www.googleapis.com/auth/classroom.profile.emails', // Access to the user's email address associated with their Google account.
  'https://www.googleapis.com/auth/classroom.profile.photos',  // Access to the user's profile photo.
  //ONLY FOR TEACHERS
  'https://www.googleapis.com/auth/classroom.coursework.students',
  "https://www.googleapis.com/auth/classroom.coursework.students.readonly",
  "https://www.googleapis.com/auth/classroom.announcements.readonly",
  //ONLY FOR STUDENTS
  'https://www.googleapis.com/auth/classroom.courses', // Access to courses a student is enrolled in.
  "https://www.googleapis.com/auth/classroom.coursework.me",
  "https://www.googleapis.com/auth/classroom.coursework.me.readonly",
  'https://www.googleapis.com/auth/classroom.rosters.readonly', // Access to course rosters, including info about teachers and classmates.
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

// Increase the request size limit (e.g., 10MB)
app.use(bodyParser.json({ limit: '100mb' }));
app.use(bodyParser.urlencoded({ extended: true, limit: '100mb' }));

// Initialize Passport
app.use(passport.initialize());
app.use(passport.session());

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
    return done(null, { profile, accessToken, refreshToken });
  }));

// Serialize and deserialize user data
passport.serializeUser(function (user, done) {
  //Including user role to display authorized data.eg: student scope can access only student functions
  const serializedUser = { ...user, role: user.profile.role }; //DOES NOT WORK AS NO ROLE IS SPECIFIED IN THE GCR API
  done(null, serializedUser);
  console.log("SCOPE OF USER", serializedUser);
});

passport.deserializeUser(function (obj, done) {
  done(null, obj);
});

app.get('/', (req, res) => {
  // This function will be executed when a GET request to the root path ("/") is made
  res.sendFile(path.join(__dirname + '/pages/login.html'));
});

// Define routes for authentication
app.get('/auth/google',
  passport.authenticate('google', {
    scope: [
      //common
      'profile',
      'email',
      'https://www.googleapis.com/auth/classroom.rosters',
      'https://www.googleapis.com/auth/classroom.profile.emails',
      'https://www.googleapis.com/auth/classroom.profile.photos',
      //teachers
      'https://www.googleapis.com/auth/classroom.coursework.students',
      'https://www.googleapis.com/auth/classroom.coursework.students',
      'https://www.googleapis.com/auth/classroom.announcements.readonly',
      //students
      'https://www.googleapis.com/auth/classroom.courses',
      'https://www.googleapis.com/auth/classroom.student-submissions.me.readonly', //own submissions+grades
      'https://www.googleapis.com/auth/classroom.rosters.readonly',
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

app.get('/success', (req, res) => {
  // //ERROR HANDLING
  if (req.isAuthenticated() && req.user.accessToken) {
    console.log("in success fn")
    //set user access token for API client
    oauth2Client.setCredentials({ access_token: req.user.accessToken });
    
    const classroom = google.classroom({ version: 'v1', auth: oauth2Client });
    classroom.userProfiles.get({userId: 'me'}, (err, response) => {
      if (err) {
        console.error('Error fetching user profile', err);
        res.status(500).send('Error fetching user profile');
        return;
      }

      const userProfile = response.data;
      // Check if the 'permissions' key exists and contains 'CREATE_COURSE' permission
      if (userProfile.permissions && userProfile.permissions.some(permission => permission.permission === 'CREATE_COURSE')) {
        // User has 'CREATE_COURSE' permission, assume they are a teacher
        req.user.role = 'teacher';
      } else {
        // User does not have 'CREATE_COURSE' permission, assume they are a student
        req.user.role = 'student';
      }

      const filePath = "userProfile.json";
      let jsonStr = JSON.stringify(userProfile);
     

      // Redirect based on the user's role
      if (req.user.role === 'teacher') {
        // User is a teacher, route to teacher-specific page
        res.redirect('/teacher');
      } else {
        // User is a student, route to student-specific page
        res.redirect('/student');
      }
    });
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
      students = undefined;
      courses.forEach(course => {
        classroom.courses.students.list(
          { courseId: course.id }, // Corrected the object structure here
          (err, response) => {
            if (err) {
              console.error("Unable to list students", err);
              res.status(500).send("Unable to list students");
            } else {
              students = response.data.students;
            }
          }
        );
      });
      // 3. GET LIST OF STUDENT SUBMISSIONS
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
              if (!Array.isArray(courseWorkList)) {
                resolveCourseWork([]);
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
          const jsonData = JSON.stringify(coursesWithSubmissions, null, 2); // Use null, 2 for pretty formatting
          
          // Set response headers to indicate JSON content and attachment
          res.setHeader('Content-disposition', 'attachment; filename=teacher_data.json');
          res.setHeader('Content-type', 'application/json');
          // Send the JSON as a downloadable attachment
          res.send(jsonData);
        })
        .catch(err => {
          res.status(500).send('Error fetching student submissions');
        });
    });
  //START STREAMLIT SERVER IF USER IS AUTHENTICATED
  startStreamlitServer();
  } else {
    res.send("You are not authenticated");
  }
});


app.get("/courses", (req, res) => {
  console.log("We are in Courses")
  const classroom = google.classroom({ version: "v1", auth: oauth2Client });
  // 1. GET LIST OF ENROLLED COURSES
  classroom.courses.list({}, (err, response) => {
    if (err) {
      res.status(500).send("Error listing student courses");
      return;
    }
    const courses = response.data.courses;
    res.send(courses)
    console.log(courses)
  })
})


app.get("/coursesubmissions", (req, res) => {
  const classroom = google.classroom({ version: "v1", auth: oauth2Client });
  const submits = [];
  const courses = req.query.courses;
  const promises = [];

  courses.forEach((course) => {
    const promise = new Promise((resolve, reject) => {
      classroom.courses.courseWork.studentSubmissions.list(
        { courseId: course.id, courseWorkId: "-" },
        (err, response) => {
          if (err) {
            console.error("Error listing student subs", err);
            reject(err);
          } else {
            const subs = response.data.studentSubmissions;
            submits.push(subs);
            resolve(subs);
          }
        }
      );
    });
    promises.push(promise);
  });

  Promise.all(promises)
    .then(() => {
      res.send(submits);
    })
    .catch((err) => {
      res.status(500).send("Error listing student subs");
    });
});

app.get("/courseworks", async (req, res) => {
  const classroom = google.classroom({ version: "v1", auth: oauth2Client });
  const courses = req.query.courses; // Assuming courses is an array of course objects

  const courseWorksPromises = courses.map((course) => {
    return new Promise((resolve, reject) => {
      classroom.courses.courseWork.list(
        { courseId: course.id },
        (err, response) => {
          if (err) {
            console.error("Error listing course works", err);
            reject(err);
          } else {
            const courseWorks = response.data.courseWork;
            resolve(courseWorks);
          }
        }
      );
    });
  });

  try {
    const courseWorksResponses = await Promise.all(courseWorksPromises);
    const allCourseWorks = courseWorksResponses.flat(); // Flatten the array of course works
    res.json(allCourseWorks);
  } catch (error) {
    console.error("Error fetching course works:", error);
    res.status(500).send("Internal Server Error");
  }
});

app.get("/student", async (req, res) => {
  const maxCourses = 15; // Set the maximum number of courses to fetch
  const finalsubs = [];
  
  if (req.isAuthenticated() && req.user.accessToken) {
    try {
      // Fetch a limited number of courses (e.g., first 10)
      const coursesResponse = await axios.get('http://localhost:5000/courses');
      const courses = coursesResponse.data.slice(0, maxCourses);

      // Fetch submissions for the limited set of courses
      const submissionResponse = await axios.get('http://localhost:5000/coursesubmissions', {
        params: { courses: courses }
      });

      const submissions = submissionResponse.data;
       // Fetch course works (assignments) data
      const courseWorksResponse = await axios.get('http://localhost:5000/courseworks', {
        params: {courses: courses}
      });
      const courseWorks = courseWorksResponse.data;
      console.log("COURSE WORK DATA----------")
      console.log(courseWorks)
      console.log("IN STUDENT ROUTE SUBS");
    
      //Rdirect to student streamlit dashboard 
      res.redirect('/streamlit_pages/overview.py');
      // Process and store the submissions
      submissions.forEach((submission) => {
        if (submission != null) {
          submission.forEach((value) => {
            finalsubs.push(value);
          });
        }
      });


      // Do something with the submissions data
      // Create a JSON string from the finalsubs array
      let jsonStr = JSON.stringify(finalsubs);
      // Specify the file path and name
      const filePath = 'finalsubs.json';
      // Write the JSON string to a file
      fs.writeFileSync(filePath, jsonStr, 'utf-8');
      console.log(`File saved as ${filePath}`);

      // Create a JSON string from the limited set of courses
      let jsonStrC = JSON.stringify(courses);
      // Specify the file path and name
      const filePathC = 'finalcourses.json';
      // Write the JSON string to a file
      fs.writeFileSync(filePathC, jsonStrC, 'utf-8');

      // Create a JSON string from the course works data
      let jsonStrCourseWorks = JSON.stringify(courseWorks);
      // Specify the file path and name for course works
      const filePathCourseWorks = 'finalcourseworks.json';
      // Write the JSON string to a file for course works
      fs.writeFileSync(filePathCourseWorks, jsonStrCourseWorks, 'utf-8');      
    } catch (error) {
      res.status(500).send("Internal Server Error");
    }
  //START STREAMLIT SERVER IF USER IS AUTHENTICATED
  startStreamlitServer();
  } else {
    res.send("You are not authenticated");
  }
});

//STREAMLIT REIDRECT ROUTES 
app.get('/streamlit_pages/overview.py', (req, res) => {
  // Redirect to the Streamlit page URL
  res.redirect('http://localhost:8501/overview'); // Update with the correct URL
});


//START STREAMLIT SERVER
function startStreamlitServer() {
  // Replace 'streamlit run' with the actual command to start your Streamlit app
  const streamlitProcess = spawn('streamlit', ['run', 'streamlit_pages/overview.py']);

  // Handle Streamlit server output (optional)
  streamlitProcess.stdout.on('data', (data) => {
  });

  // Handle Streamlit server errors (optional)
  streamlitProcess.stderr.on('data', (data) => {
  });

  // Handle Streamlit server exit (optional)
  streamlitProcess.on('close', (code) => {
  });
}


//START NODE.JS APP WITH STREAMLIT SUB PROCESS
app.listen(5000, () => {
  console.log('Server started on http://localhost:5000');
});
