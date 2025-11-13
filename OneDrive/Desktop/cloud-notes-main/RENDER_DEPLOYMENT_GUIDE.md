# Deploying Cloud Notes App on Render

This guide provides step-by-step instructions to deploy your Flask-based Cloud Notes App on Render, a modern cloud platform for web applications.

## Prerequisites

Before deploying, ensure you have:

- A GitHub account with your project repository
- A MongoDB Atlas account (free tier available)
- Basic familiarity with Git and command line

## Step 1: Prepare Your Project

Your project should include these files (already set up):

- `app.py` - Main Flask application
- `requirements.txt` - Python dependencies
- `render.yaml` - Render configuration (optional)
- `templates/` - HTML templates
- `static/` - CSS and static files
- `.gitignore` - To exclude sensitive files

## Step 2: Set Up MongoDB Atlas

1. Go to [MongoDB Atlas](https://cloud.mongodb.com/) and create a free account
2. Create a new cluster (M0 Sandbox - free)
3. Set up a database user:
   - Go to "Database Access"
   - Click "Add New Database User"
   - Choose "Password" authentication
   - Set username and password
4. Configure network access:
   - Go to "Network Access"
   - Click "Add IP Address"
   - Choose "Allow Access from Anywhere" (0.0.0.0/0)
5. Get your connection string:
   - Go to "Clusters"
   - Click "Connect"
   - Choose "Connect your application"
   - Copy the connection string
   - Replace `<password>` with your database user password

## Step 3: Create Render Account

1. Visit [render.com](https://render.com/)
2. Sign up for a free account
3. Connect your GitHub account to Render

## Step 4: Deploy on Render

### Create New Web Service

1. In your Render dashboard, click **"New +"**
2. Select **"Web Service"**

### Connect Repository

1. Choose your GitHub repository from the list
2. If your repo isn't listed, paste the repository URL

### Configure Service Settings

Fill in the following details:

- **Name**: `cloud-notes-app` (or your preferred name)
- **Runtime**: `Python`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`
- **Plan**: `Free` (750 hours/month)

### Set Environment Variables

1. Scroll to the **"Environment"** section
2. Click **"Add Environment Variable"**
3. Add these variables:

   | Key | Value |
   |-----|-------|
   | `SECRET_KEY` | Generate a secure random string (32 characters). You can use: `openssl rand -hex 32` in terminal or an online generator |
   | `MONGODB_URI` | Your MongoDB Atlas connection string (e.g., `mongodb+srv://username:password@cluster.mongodb.net/notes_app`) |

   **Important**: Never commit these values to your Git repository!

### Deploy

1. Click **"Create Web Service"**
2. Render will start building your application
3. The build process takes 2-5 minutes
4. Once complete, you'll get a URL like: `https://cloud-notes-app.onrender.com`

## Step 5: Test Your Deployment

1. Visit the provided URL
2. Test the application:
   - Click "Create an account" to register
   - Login with your credentials
   - Add a new note
   - Edit the note
   - Delete the note
3. Verify database connectivity (notes should persist)

## Step 6: Monitor and Maintain

### View Logs
- In Render dashboard, go to your service
- Click **"Logs"** tab to view real-time logs

### Update Environment Variables
- Go to **"Environment"** in service settings
- Update variables as needed (e.g., change database password)

### Custom Domain (Optional)
- In service settings, go to **"Settings"**
- Add your custom domain
- Configure DNS records as instructed

## Troubleshooting

### Build Failures
- Check the build logs for errors
- Ensure `requirements.txt` includes all dependencies
- Verify Python syntax in `app.py`

### Runtime Errors
- Check application logs
- Verify environment variables are set correctly
- Ensure MongoDB Atlas connection string is valid

### Database Connection Issues
- Confirm MongoDB Atlas allows connections from anywhere (0.0.0.0/0)
- Check username/password in connection string
- Verify database name in connection string

### Static Files Not Loading
- Flask serves static files automatically
- Check file paths in templates (should use `{{ url_for('static', filename='styles.css') }}`)

## Cost Information

- **Free Tier**: 750 hours/month, perfect for development and light usage
- **Paid Plans**: Start at $7/month for more resources
- **MongoDB Atlas**: Free tier (512MB storage)

## Security Notes

- Environment variables keep secrets secure
- HTTPS is enabled automatically by Render
- Consider restricting MongoDB Atlas IP access after testing
- Regularly update dependencies for security patches

## Next Steps

- Set up automated deployments (push to GitHub triggers Render rebuild)
- Add monitoring/alerts in Render dashboard
- Consider backup strategies for MongoDB Atlas
- Implement additional security measures (rate limiting, input validation)

For more help, refer to Render's [official documentation](https://docs.render.com/).
