# Microsoft Graph Setup - Final Steps

## You've completed most of the setup! Now we need to enable "Public client flow" for device code authentication.

### Steps to Complete in Azure Portal:

1. Go back to your app registration "Buddy Email Reader" in Azure Portal
2. In the left menu, click on "Authentication"
3. Scroll down to "Advanced settings" section
4. Find "Allow public client flows"
5. Set it to **YES**
6. Click "Save" at the top

### Why is this needed?
- We're using "device code flow" for authentication, which allows the script to authenticate without storing your password
- You'll authenticate once in a browser, and the token will be cached for future use
- This is more secure than Basic Auth IMAP and works around the Microsoft 365 Basic Auth block

### What happens next?
1. When you run the Mployer scraper, it will detect MFA is required
2. It will prompt you to visit a URL and enter a code in your browser
3. After you authenticate once, the token is cached and won't ask again (until it expires)
4. The script will automatically retrieve MFA codes from your email

### Ready to test?
Once you've enabled "Allow public client flows" in Azure, let me know and we'll test the full flow!
