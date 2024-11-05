# linkedin_statistical_inference

Is it better to send LinkedIn connection requests with a personalized message or leave them blank? That’s the question I try to answer in this repo.

To prove that one approach has a higher acceptance rate, we need to conduct an A/B test. The main idea of an A/B test is randomization, so the decision of who gets a blank request and who gets a message should be completely random. If I try to do this manually, I will introduce my bias into the test, and it wouldn’t be within the rules of A/B testing.

That’s why it should be completely randomized. The architecture below automates this process to eliminate my bias. Here is how it works:
- A Cron job on a Raspberry Pi activates orchestrator.sh, and any error that occurs after that goes to cron.log.
- An arrow under DAILY PROCESS represents a randomized time delay between actions, so after Cron job activation, there is a delay before main.py.
- main.py opens the Google spreadsheet with LinkedIn links and a Chromium browser, then it opens profiles, pulls needed info, and sends them requests.
- To be on the safe side, counter updates happen after some time in a separate file to ensure that each day the bot works with new profiles.
- LinkedIn is tricky, so checking_invites.py verifies that these people are added and logs this in a spreadsheet.
- checking_accepts.py pulls people who accepted my invite so that we can conduct an A/B test afterward.
- LinkedIn doesn’t allow more than 700 sent requests, so removing_old_invite_requests.py keeps it under 600.




  Here is what the spreadsheet looks like (private data is hidden, of course):
- The A/B test was recently completed with the following stats:

I will be releasing a Jupyter Notebook with statistical tests soon, but a preliminary analysis confirms the hypothesis that sending a connection request with a message works much better (all statistics and p-values support this).
