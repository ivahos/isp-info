This script needs python3 installed in addition to the python module matplotlib.
to install this on debian run the command apt install python3 python3-matplotlib
you will also need to install php and enable this in your webserver
you also need to install ooklas cli version of speed test on a machine at home that is up at all times. I use a VM running debian for this:
curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | sudo bash
sudo apt install speedtest

You also need to install the 2 crontab entries in the crontab file on the same machine you installed the cli version of speed test on. It will use scp to copy the result to your webserver so that it can be accessed by the generate_graph.py scriptt


<pre>
files:
example.html                - Example on how to  use the python script to generate the speedtesrt graphs 
crontab                     - crontab instructions for running the actual speedtests collectin the output in a file and copying it to the webserver
generate_speedtest_graph.py - python script for creating the graph
</pre>
