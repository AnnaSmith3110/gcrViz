const express = require('express');
const mongoose = require('mongoose');

const url = 'mongodb://127.0.0.1:27017/testing_database';
const port = 3000;
const app = express();

mongoose.connect(url, { useNewUrlParser: true, useUnifiedTopology: true })
    .then(() => {
        console.log('Database connected');

        // Define a Mongoose schema for your data
        const jsonDataSchema = new mongoose.Schema({
            data: Object, // Assuming you want to store a JSON object
        });

        // Create a Mongoose model based on the schema
        const JsonData = mongoose.model('JsonData', jsonDataSchema);

        // Predefined JSON data
        const predefinedData = {
            name: 'Life Is It?',
            email: 'life@gmail.com',
            allowed: 'False'
        };

        // Insert predefined JSON data into the MongoDB
        const insertPredefinedData = async () => {
            try {
                // Create a new document based on the JsonData model
                const newJsonData = new JsonData({
                    data: predefinedData, // Use the predefined JSON data
                });

                // Save the new JSON data to the database
                await newJsonData.save();
                console.log("Inserted predefined JSON data successfully");
            } catch (err) {
                console.error('Error inserting predefined JSON data:', err);
            }
        };

        // Call the function to insert predefined data when the app starts
        insertPredefinedData();
    })
    .catch(err => {
        console.error('Database connection error:', err);
    });

// Middleware to parse JSON requests
app.use(express.json());

app.get('/', (req, res) => {
    res.send('<h1>Hello from Node.js app</h1>');
});

app.listen(port, () => {
    console.log('Server is running at port ' + port);
});