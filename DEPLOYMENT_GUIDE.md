# EcoMonitor Deployment Guide

This guide provides instructions on how to deploy the EcoMonitor application to production environments:
- Backend: PythonAnywhere
- Frontend: Netlify

## Backend Deployment (PythonAnywhere)

1. **Create a PythonAnywhere Account**
   - Sign up for a free account at [PythonAnywhere](https://www.pythonanywhere.com)

2. **Create a Web App**
   - Go to the Web tab
   - Click "Add a new web app"
   - Select "Flask" and Python 3.11 (or closest available version)
   - Choose a Python Web framework (Flask)
   - Set up the path to your WSGI configuration file

3. **Clone the Repository**
   - In the PythonAnywhere Bash console:
   ```bash
   git clone https://github.com/yourusername/ecomonitor.git
   cd ecomonitor
   ```

4. **Create Requirements File**
   - Create a requirements.txt file with these dependencies:
   ```
   beautifulsoup4==4.12.3
   email-validator==2.1.1
   flask==3.0.3
   flask-cors==4.0.0
   flask-sqlalchemy==3.1.1
   gunicorn==23.0.0
   pandas==2.2.1
   psycopg2-binary==2.9.9
   python-dotenv==1.0.1
   requests==2.31.0
   trafilatura==1.7.0
   ```

5. **Install Dependencies**
   - In the PythonAnywhere Bash console:
   ```bash
   pip install -r requirements.txt
   ```

6. **Set Up Environment Variables**
   - Go to the Web tab
   - Scroll down to the "Environment variables" section
   - Add your API keys:
     ```
     AQICN_API_KEY=your_aqicn_api_key
     EBIRD_API_KEY=your_ebird_api_key
     OPENAQ_API_KEY=your_openaq_api_key
     ```

7. **Configure WSGI File**
   - Update the WSGI configuration file to point to your Flask app
   - It should look similar to this:
   ```python
   import sys
   import os
   
   # Add your project path
   path = '/home/yourusername/ecomonitor'
   if path not in sys.path:
       sys.path.append(path)
   
   # Set environment variables if needed
   os.environ['FLASK_ENV'] = 'production'
   
   # Import your flask app
   from app import app as application
   ```

8. **Update CORS Settings**
   - Edit the app.py file to update the allowed origins with your Netlify domain
   - Remove the wildcard '*' entry for security

9. **Reload Web App**
   - Go to the Web tab and click the "Reload" button for your web app

## Frontend Deployment (Netlify)

1. **Create a Netlify Account**
   - Sign up for a free account at [Netlify](https://www.netlify.com)

2. **Prepare the Frontend Files**
   - Create a separate repository for the frontend (or a separate branch)
   - Copy all files from the 'static' directory into this repository

3. **Update API Configuration**
   - Open `assets/js/main.js`
   - Update the `API_CONFIG` object with your PythonAnywhere URL:
   ```javascript
   const API_CONFIG = {
       // Development (local) environment
       development: {
           baseUrl: ''  // Empty string means relative to current domain
       },
       // Production environment (when deployed)
       production: {
           baseUrl: 'https://yourusername.pythonanywhere.com'  // Your PythonAnywhere URL
       }
   };
   ```

4. **Add a _redirects File**
   - Create a file named `_redirects` in the root directory with the content:
   ```
   /* /index.html 200
   ```
   - This ensures proper SPA routing

5. **Deploy to Netlify**
   - Connect Netlify to your Git repository
   - Set build settings if necessary (typically not needed for static sites)
   - Deploy the site

6. **Set Up Custom Domain (Optional)**
   - Add your custom domain in the Netlify site settings
   - Configure DNS according to Netlify's instructions

## Testing the Deployment

1. Open your Netlify URL in a browser
2. Test all the features:
   - Dashboard view
   - AQI monitoring with current location
   - Deforestation data visualization
   - Bird information and visualization
   - Environmental news
   - Impact calculator

## Troubleshooting

### CORS Issues
- If you see CORS errors in the browser console, check:
  - The CORS configuration in app.py
  - Make sure your Netlify domain is properly added to allowed_origins

### API Key Issues
- If API data isn't loading, verify:
  - All API keys are correctly set in PythonAnywhere environment variables
  - Keys have proper permissions and quotas

### 404 Errors on Netlify
- Make sure the _redirects file is properly created
- Verify that there are no routing issues in the frontend code

### PythonAnywhere Errors
- Check the error logs in the PythonAnywhere Web tab
- Make sure your WSGI file is correctly configured
- Ensure all dependencies are installed

## Security Notes

1. Never expose API keys in the frontend code
2. Remove the wildcard '*' from CORS settings in production
3. Use HTTPS for all connections
4. Consider implementing proper authentication for production use

## Maintenance

- Regularly update dependencies
- Monitor API limits
- Check for data source changes or deprecations