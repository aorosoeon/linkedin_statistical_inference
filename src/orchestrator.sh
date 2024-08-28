#!/bin/bash
#this file is launched by cron at 10:30 am. if something goes wrong - check ab_linkedin_cron.log in home/arsenchuzhykov
source /home/arsenchuzhykov/linkedin_and_telegram/bin/activate
sleep $((120 + RANDOM % 840))s #2-15
python /home/arsenchuzhykov/Desktop/final_ab_linkedin_raspberry/main.py
sleep $((300 + RANDOM % 240))s #5-8
python /home/arsenchuzhykov/Desktop/final_ab_linkedin_raspberry/updating_counter.py
sleep $((660 + RANDOM % 240))s #11-14
python /home/arsenchuzhykov/Desktop/final_ab_linkedin_raspberry/checking_invites.py
sleep $((540 + RANDOM % 240))s #9-13
python /home/arsenchuzhykov/Desktop/final_ab_linkedin_raspberry/checking_accepts.py
sleep $((360 + RANDOM % 360))s #6-12
python /home/arsenchuzhykov/Desktop/final_ab_linkedin_raspberry/removing_old_invite_requests.py
sleep $((300 + RANDOM % 360))s #5-10
deactivate