 """
        Name:

            SideBySide.py

        Description:

            Given two video files, runs them concurrently in two side by side
            instances of ffplay. Ths is very useful when you have processed a
            video and want to compare the original with the processed version.

            If you want to test a process (e.g. a filter) before processing the
            entire video, run the script by specifying -same as the second video
            as in

                SideBySide video1.mp4 -same  -vf smartblur=5:0.8:0

            Try the following filter to increase the contrast

                -vf colorlevels=rimin=0.2:gimin=0.2:bimin=0.2

            Convert to greyscale

                -vf colorchannelmixer=.3:.4:.3:0:.3:.4:.3:0:.3:.4:.3

            Convert to sepia

                -vf colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131

            adjust gamma/saturation

                -vf eq=gamma=1.5:saturation=1.3 

        Requires:

            Python version 3.8 or later
            ffmpeg (which includes ffplay)
            autoit (version 3)

        Usage:

            SideBySide video1 video2

        Notes:

            Regardless of the dimensions of the input videos, they will always be scaled so that
            they can be placed side by side, each filling just under half the width of the display.

            I haven't verified this, but I'm assuming that manipulating windows by handle rather
            than by name is more efficient which may be a consideration because I do it repeatedly
            in the wait loop at the bottom.

        Audit:

            2021-08-31  rj  original code

    """

    import os
    import re                   #needed to extract video frame size
    import tkinter              #needed to get display size
    import win32com.client      #needed to create the AutoId com object
    import subprocess           #needed to run ffprobe.exe
    import sys
    import time


    def DisplaySize():
        """Returns the monitor display resolution as (width, height)"""
        root = tkinter.Tk(None)
        return root.winfo_screenwidth(), root.winfo_screenheight()

    def VideoSize(file):
        """Returns the frame size of a video as (width, height)"""

        #Run ffprobe to get video info
        res = subprocess.run(['ffprobe', '-i',  file], shell=True, stderr=subprocess.PIPE, text=True)

        #Extract frame size
        for line in res.stderr.split('\n'):
            if 'Video:' in line:
                if (search := re.search(' \d+x\d+ ', line)):
                    w,h = line[1+search.start():search.end()-1].split('x')
                    return int(w), int(h)

        return 0, 0

    def WaitFor(title, timeout):
        """Waits for up to timeout seconds for the window with the given title to be active"""
        timeout *= 10
        while not aut.WinActive(title):
            time.sleep(0.1)
            timeout -= 1
            if timeout == 0:
                print('expired')
                sys.exit()
        return


    #check for sufficient number of parameters
    if len(sys.argv) < 3:
        print("""
    SideBySide video1 video2

        Displays two videos side by side for comparison. This is useful to see
        before and after video effects such as colour/contrast manipulation or
        scaling.

        If you want to try some ffmpeg filters before applying them to a complete
        video you can supply ffmpeg parameters ad hoc. To use the same video for
        both panels specify '-same' as the second video. For example, to see the
        effect of a gamma correction you can type:

            sidebyside video.mp4 -same -vf eq=gamma=0.9

        To save you the trouble of remembering ffmpeg filters several shortcuts
        are provided as follows:

            sidebyside video.mp4 -same -gamma 0.9        apply gamma correction
            sidebyside video.mp4 -same -contrast .12     apply contrast correction
            sidebyside video.mp4 -same -grey             convert to greyscale
            sidebyside video.mp4 -same -sepia            convert to sepia
    """)
        sys.exit()

    #get file names and command line options
    video1 = sys.argv[1]
    video2 = sys.argv[2]

    if video2 == '-same':
        video2 = video1

    if len(sys.argv) > 3:
        if sys.argv[3].lower() == '-grey':
            args = '-vf colorchannelmixer=.3:.4:.3:0:.3:.4:.3:0:.3:.4:.3'
        elif sys.argv[3].lower() == '-sepia':
            args = '-vf colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131'
        elif sys.argv[3].lower() == '-contrast' and len(sys.argv) > 4:
            cval = sys.argv[4].strip('0')
            args = '-vf colorlevels=rimin=%s:gimin=%s:bimin=%s' % (cval, cval, cval)
        elif sys.argv[3].lower() == '-gamma' and len(sys.argv) > 4:
            gval = sys.argv[4].strip('0')
            args = '-vf eq=gamma=%s' % gval
        else:
            args = ' '.join(sys.argv[3:])
    else:
        args = ''

    if not os.path.isfile(video1):
        print('Could not find:', video1)
        sys.exit()

    if not os.path.isfile(video2):
        print('Could not find:', video2)
        sys.exit()

    #create unique window titles
    title1 = '1: ' + video1
    title2 = '2: ' + video2

    #create the AutoIt com object
    aut = win32com.client.Dispatch("AutoItX3.Control")
    aut.Opt("WinTitleMatchMode", 3)     #3 = Match Exact Title String)

    #get the display width and height, and same for video
    dw,dh  = DisplaySize()
    vw,vh  = VideoSize(video1)
    aspect = vw / vh

    #Calculate size and position of playback windows
    vw = int((dw-20) / 2)
    vh = int(vw / aspect)
    x1 = '10'
    y1 = '35'
    x2 = str(int((dw/2)) + 5)
    y2 = '35'

    #set up the commands to run ffplay
    #  -v 0 suppresses the standard ffplay output
    #  -window_title guarantees unique windo titles even if using the same video
    cmd1 = 'ffplay -v 0 -window_title "' + title1 + '" -i "' + video1 + '"' \
         + ' -x ' + str(vw) + ' -y ' + str(vh) + ' -left ' + x1 + ' -top ' + y1
    cmd2 = 'ffplay -v 0 -window_title "' + title2 + '" -i "' + video2 + '" ' + args \
         + ' -x ' + str(vw) + ' -y ' + str(vh) + ' -left ' + x2 + ' -top ' + y2

    #Run ffplay on the first video. Wait for it to be active then get the handle.
    print('\n' + cmd1)
    if (p1 := aut.Run(cmd1)) == 0:
        print('Could not start ffplay.exe')
        sys.exit()

    #aut.WinWaitActive(title1, '', 5)
    WaitFor(title1, 5)
    handle1 = aut.WinGetHandle(title1)
    handle1 = '[HANDLE:%s]' % handle1
    #print('video 1 active - handle is', handle1)

    #Run ffplay on the second video. Wait for it to be active then get the handle.
    print('\n' + cmd2)
    if (p2 := aut.Run(cmd2)) == 0:
        print('Could not start ffplay.exe')
        sys.exit()

    #aut.WinWaitActive(title2, '', 5)
    WaitFor(title2, 5)
    handle2 = aut.WinGetHandle(title2)
    handle2 = '[HANDLE:%s]' % handle2
    #print('video 2 active - handle is', handle2)

    #This loop will terminate on CTRL-C or when both video players are closed
    try:
        while aut.WinExists(handle1) or aut.WinExists(handle2):
            time.sleep(1)
    except:
        pass

