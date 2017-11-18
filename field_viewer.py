# -*- coding: utf-8 -*-
"""
Script that coordinates audio and video
and makes a movie out of it -
this allows for a combined visualisation of the
bats, mic and the recording rms - or other such parameters

Created on Mon Jul 17 22:57:09 2017

@author: tbeleyur
"""
import scipy.signal as signal
import numpy as np
from scipy.io import wavfile as wav
import pandas as pd
import peakutils
import cv2
import easygui as eg
import glob
import os



# TO DO :
# PRIOTIRY:
# > the EASYGUI package is the latest ..why is my Spyder refusing to work with it ?
# 2) write a function which checks if the total number of frames and the audio recordings match !!


class Gamana:

    def __init__(self):
        self.magnif_factor = 100
        self.baseline_radius = 10

    def compile_AV(self,folder_address,input_video_file,output_video_name,audio_blocksize=320,blocks_per_frame=24,DLTdv5=True,**kwargs):
        '''
        function which finds,loads raw data files for the actual
        video with audio overlaying and saving

        Inputs:
            folder_address: string. address to the folder with all the input files
            input_video_file: string. name of video file.
            output_video_name: string. Final name of video file - with .avi
            audio_blocksize: +ve integer. number of samples over which rms is calculated.
            blocks_per_frame: +ve integer. number of rms values  per frame.
            DLTdv5: boolean. Default as True. Whether the xy coordinates in csv files were digitised using DLTv5


            **kwargs:
            bat_positions: highlight bat positions across frames. as of 29/7/2017 not yet supported
            vid_sig_fps

        Outputs:
        produces a video with mic rms overlayed on the mic positions


        '''

        if audio_blocksize < 0 or not( type(audio_blocksize) is int )  :
            raise TypeError('audio_blocksize must be a positive integer')

        if blocks_per_frame < 0 or not( type(blocks_per_frame) is int )  :
            raise TypeError('blocks_per_frame must be a positive integer')

        # search for files with the following wildcard terms
        synchro_channel = glob.glob(folder_address + 'synchro*.wav')

        micspos_csv =   glob.glob(folder_address+'micpos*.csv')
        # THINGS TO DO : 11/8/2017 , write a function to make sure that
        # MIC numbers fit a particular format - or somehow get them
        # in an ascending order in the list
        mic_wavs = glob.glob(folder_address + 'Mic*.wav')

        func_inpts = {'mic positions': micspos_csv,'mic files':mic_wavs}

        # disp error if some of the files have not been found in folder
        for entry in func_inpts:
            if len(func_inpts[entry]) == 0:
                msg =( 'Unable to find file name for '+ entry+'. '
                'Please check if the input files are name accordingly or exist in folder'
                )
                raise Exception( msg )
        try:
            fs, synchron = wav.read(synchro_channel[0])
            f_times = self.extract_frametimes(synchron,fs,kwargs)
        except:
            print('ATTENTION/ACHTUNG: Unable to read synchro channel or get frame samples- assuming 1st frame was taken at first audio sample ')


        # 1/8/2017 : functionality to be added :
        #        >>>> check if the block size * blocks_per_frame
        # match up with the np.diff(f_times) -- and warn the user if
        # they don't match.

        # if the synchro channel is given , then use it - otherwise assume the video-audio begins
        # from the 1st sample on!

        if len(synchro_channel) >0:
            rms_blocked = [ self.rms_calculator( each_file,audio_blocksize,synchro_channel = f_times)['chunked_rmsdata'] for each_file in mic_wavs ]
        else:
            rms_blocked = [ self.rms_calculator( each_file,audio_blocksize)['chunked_rmsdata'] for each_file in mic_wavs ]

        mics_rms = np.column_stack(rms_blocked)

        np.save(folder_address+'mics_rms.npy',mics_rms)

        print('\n blockrms file written successfully')

        micpos = np.asanyarray(self.read_csv_files(micspos_csv[0])).flatten()
        micpos = micpos.astype('int16')

        output_video = folder_address+ output_video_name
        input_video  = folder_address + input_video_file

        print( ' beginning compiled video playback')

        self.play_AV(input_video,output_video,mics_rms,micpos,blocks_per_frame,DLTdv5,**kwargs)

        print ('compiled video playback ended')

        return()



    def play_AV(self,videoin_address,videoout_address,mics_rms,mics_pos,rms_vals_per_frame=24,DLTdv5=True,**kwargs):
        '''
        function which plays the vide and plots audio rms

        Inputs:
            videoin_address: string. path to video file

            videoout_address:string. path to output video file with overlay

            mics_rms : N_samples x num_channels np.array of recorded data from the
                    inputs mics whose rms values will be plotted

            mics_pos: 1 x (num_mics x 2) np.array with the x,y pixel coordinates

            rms_vals_per_frame: integer. Number of rms values that are to be plotted
                            for one frame.

            DLTDv5 : Boolean. Default= True. Whether the xy coordinates were digitised
                    from DLTdv5
            **kwargs:
            bat_positions: num_video_frames x (num_batsx2) np.array, with the xy pixel
                            coordinates over time
            orig_fps: +ve integer. FPS at which the original video was recorded at
                        also decides the FPS at which the output video is saved
                        Default of 25 fps unless stated otherwise.



        '''



        # now let's load the video, and update the audio accordingly :
        try:
            cap =  cv2.VideoCapture(videoin_address)
            num_frames = int ( cap.get(cv2.CAP_PROP_FRAME_COUNT))
            height,width = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_shape = (height,width)
        except:
            raise ValueError('Unable to load video - please check file or address')

        if 'orig_fps' in kwargs:
            frame_rate = int(kwargs['orig_fps'] )
        else:
            frame_rate = 25.0

        # TO BE IMPLEMENTED : calculate video and audio durations and check if
        # they match
        #av_durns_okay = check_audio_video_durations(audio_duration,num_frames,)
        # check if the  difference of audio and video durations
        # is more than 1 second - and get manual input to proceed or not
    #    if not ( (video_durn <= audio_durn + 1.0) or (video_durn >= audio_durn + 1.0) ):
    #
    #        waiting_for_user = True
    #
    #        while waiting_for_user:
    #
    #            user_msg = 'There is a >1 second audio-video difference in length. Do you want to continue? Y for yes, N for no  :'
    #            user_decision = raw_input(user_msg)
    #
    #
    #            if user_decision == 'Y':
    #                waiting_for_user = False
    #            elif user_decision =='N':
    #                break
    #            else:
    #                print('wrong input please give valid input')
    #





        try:
            fourcc = cv2.VideoWriter_fourcc(*'DIVX')

            vid_out_frame_rate = 30

            vid_out = cv2.VideoWriter(videoout_address,fourcc,vid_out_frame_rate,(width,height))
        except:

            raise Exception('Unable to open videowriter object, check videoout_address')




        # check if num mics and num audio channels match:

        num_mics, num_audio_channels = self.check_channels_to_mics(mics_pos,mics_rms)

        num_total_blocks = mics_rms.shape[0]

        # get all the mic positions:
        mics_x = mics_pos[0::2]
        mics_y = mics_pos[1::2]

        if DLTdv5:
            mics_y = self.conv_DLTdv5_to_opencv2(mics_y,frame_shape)


        disp_frame = 0
        audio_blocknum = 0
        dispd_blocks = 0

        print('...beginning rms on video overlaying')
        while disp_frame < num_frames :

            dispd_blocks = 0
            #cap.set(1,disp_frame); # Where frame_no is the frame you want
            ret, frame = cap.read() # Read the frame

            while (dispd_blocks < rms_vals_per_frame) & (audio_blocknum < num_total_blocks):


                rms_radii =  np.apply_along_axis(self.conv_rms_to_radius,0,mics_rms,audio_blocknum)

                for each_mic in range(num_mics):
                    cv2.circle(frame, (mics_x[each_mic] , mics_y[each_mic] ), rms_radii[each_mic], (100,300,525), 1 )


                cv2.putText(frame,str(disp_frame/float(frame_rate)),(width-100,50),cv2.FONT_HERSHEY_SIMPLEX, 1, 255)

                # TO BE ADDED HERE: plotting of bat positions - when given in kwargs
                #if 'bat_positions' in kwargs:
                 #   num_bats

                # TO BE ADDED HERE 11/8/2017:
                # add a stamp at the beginning or end of the file which describes the
                # block size, blocks per frame used and the original fps at which the
                # video was recorded


                cv2.imshow('GAMANA', frame) # show frame on window


                # write the frame with all the overlayed information
                vid_out.write(frame)

                ch = 0xFF & cv2.waitKey(1)

                if ch == ord('q') :
                    disp_frame = num_frames+1


                audio_blocknum +=1
                dispd_blocks +=1




            disp_frame += 1

        cap.release()
        vid_out.release()
        cv2.destroyAllWindows()

        success_msg = 'video and mic rms data succesfully compiled \n Output file written to : \n', videoout_address

        return(success_msg)



    def rms_calculator(self,wav_file,block_size,**kwargs):
        '''
        splits a wav file into multiple chunks of block_size
        and calculates the rms value of these blocks

        Input    :
        wav_file : string. address of the WAV file
        block_size: integer. number of samples over which the rms will be
                calculated. DefAULT VALUE 320 SAMPLES

        **kwargs:
            synchro_channel:
                which has frame time information. Default = True. This decides
                the first sample

        Outputs:
        rms_chunked : 1x num_chunks np.array. num_chunks is
                    rounded up after calculating wav_file.size / block_size

        '''
        fs,recording = self.load_wavfile(wav_file)

        print(wav_file)

        try:
            block_size = int(block_size)
        except:
            ValueError('Problem converting block_size into integer')

        # if there's no synchro_channel - then assume that the video starts at the
        # 0th sample

        if not('synchro_channel' in kwargs):
            start_segment = 0
            print ( ' \n assuming that audio and video recording started from 0th sample on sychronously')

        else:
            print('\n synchro channel found - using given frame indices')

            start_segment = np.min( kwargs['synchro_channel']  )

        print('the start index is ',start_segment)
        end_segment = start_segment+ block_size -1

        rms_chunked_list = []

        # as of 18/7/2017 the script calculates rms in blocks only to
        # the right of the first frame. Data from the left of this
        # sample is *ignored*

        #  round up to avoid losing out data at the very end

        num_chunks = int(np.ceil( (recording.size-start_segment) /float(block_size)))

        i = 0
        for k in range(num_chunks):
            i +=1

            try:
                rec_segment = recording[start_segment:end_segment ]

            except:
                # in the end of the recording, when the block size
                # exceeds the length of the array
                rec_segment = recording[start_segment:]

            else :
                #print('start segment index',start_segment,'i:',i)
                ValueError('Indexing problem with extracting last segment of recording..')

            rms_chunk = np.std(rec_segment)
            rms_chunked_list.append(rms_chunk)

            start_segment += block_size
            end_segment += block_size


        print('num of chunks: ',i)

        try:
            rms_chunked = np.asanyarray(rms_chunked_list)
        except:
            Exception('error in converting rms_chunked_list into array')

        chunked_rms_data = {'chunked_rmsdata':rms_chunked,'block_size':block_size}

        return(chunked_rms_data)



    def load_wavfile(self,wav_file):
        try:
            fs,recording = wav.read(wav_file)

            if np.max(np.abs(recording)) >1:
                raise ValueError('The wav file is not between -1 and +1 , please check')
        except:
            Exception('Problem reading wav file')



        return(fs,recording)


    def extract_frametimes(self,synchron_channel,fs=192000,vid_sig_Hz = 25, **kwargs):
        '''
        when a square wave + high frequency signal is
        fed in as a single channel recording - then it extracts
        the sample index of the maximum value on the rising edge.

        IMPORTANT : The function expects a 25/30 Hz signal

        Inputs:
        synchron_channel: 1xN samples np.array with square wave. The frames
                are recorded when the values hit their peak +ve value.
        fs

        '''

        # LP the recording, find a zero crossing with a +ve slope
        # and then find the position of highest values in its vicinity

        if not (vid_sig_Hz in [25,30]):
            print('nonstandard video sync signal (other than 25/30 Hz) !')

        # lowpass filter the signal
        if 'lowpass_freq' in kwargs:
            if kwargs['lowpass_freq'] <= [25,30]:
                ValueError('lowpass frequency too low - please check value once more')

            else:
                b,a = signal.butter(8, kwargs['lowpass_freq']/float(fs), 'low' )

                # use filtfilt to get zero phase delay
                synchron_lp = signal.filtfilt(b,a,synchron_channel)

                # now extract all points where the transition from -ve to +ve occurs :

                trans_indxs = self.get_frame_times(synchron_lp,fs)
        else:
            trans_indxs = self.get_frame_times(synchron_channel,fs)


        return(trans_indxs)



    def get_frame_times(self,synchron_channel,fs,**kwargs):
        '''
        extracts the sample points at which the
        frame was recorded. In the TeAx FLIR Tau2 cores
        , frames are recorded when voltage increases above a
        particular +ve voltage.

        Inputs:
        synchron_channel: 1 x N np.array channel with
                        square waves of 25 or 30 Hz.
                        IMPORTANT: currently no other video frame rate is
                        supported
        fs: integer, sampling rate
        **kwargs:
            vid_sig_fps : integer. fps at which the sync signal triggers the camera

        Outputs:
        frame_inds: 1 x num_frames np.array. Has the indices at which the square wave
                    rises to its maximum value - this is the sample at which
                    frame recording was triggered in the camera


        '''

        # remember TO CHANGE THIS WHEN IT'S IN CLASS MODE ;

        threshold = np.max(synchron_channel) * 0.3

        if 'vid_sig_fps' in kwargs:
            print('vid_sig_fps given ',kwargs['vid_sig_fps'],' will be used to extract peaks')
            min_pk_2_pk = ( 1 / float(kwargs['vid_sig_fps']) ) *fs
        else:
            print ('No video_sig_fps given, assuming minimum peak-to-peak for 30Hz signal')
            min_pk_2_pk = (1/30.0)*fs

        diff_synchron = np.diff(synchron_channel)

        # this is the approximate peaks in the channel got from the
        # derivative
        aprx_pks = peakutils.indexes(diff_synchron,thres=threshold, min_dist = min_pk_2_pk)


        # now we get the precise maximum within +/- 100 sampls of this approximate position

        precise_pks = []
        for each_aprx_pk in aprx_pks:

            # when the aprx_pk is in the 'middle' of the array
            left_edge = each_aprx_pk - 100
            right_edge = each_aprx_pk + 100
            search_segment = synchron_channel[left_edge:right_edge]

            if left_edge <0:
                # when the aprx_pk is to the extreme left of the array
                left_edge = 0
                right_edge = each_aprx_pk + 100
                search_segment = synchron_channel[left_edge:right_edge]

            if right_edge > (synchron_channel.size -1) :
                # when the aprx_pk is to the extreme right of the array
                left_edge = each_aprx_pk - 100
                right_edge =  (synchron_channel.size -1)
                search_segment = synchron_channel[left_edge:]

            # add on the local search_segment index maxima to get
            # the location of the +ve peak in the whole recording

            if np.max(search_segment) >= threshold:
                search_seg_argmax = np.argmax(search_segment)
                synchron_channel_indx = left_edge + (search_seg_argmax - 1 )
                precise_pks.append(  synchron_channel_indx )
            else :
                pass

        frame_inds = np.asanyarray(precise_pks)


        return(frame_inds)




    def conv_DLTdv5_to_opencv2(self,y_coods,frame_shape):
        '''
        converts the y image coordinates
        from DLTdv5 into opencv2 compatible coordinates
        Inputs:
        y_coods : N x 1 np.array. with y coordinates
        frame_shape : 1 x 2 np.array with integer values of pixel height and width of
                    frame
        '''

        frame_height = frame_shape[0]

        y_compatible = frame_height - y_coods
        print  ('..coordinates made opencv2 compatible')
        return(y_compatible)

    def conv_rms_to_radius(self,rms_array,index):
        '''
        converts a np.array with rms values into a viewable
        circle with rms proportional radius in pixels
        '''

        rms_value = rms_array[index]

        if rms_value < 0:
            raise ValueError('rms value cannot be less than 0 - please check how rms was calculated')
        else:
            radius = int(  np.around( self.magnif_factor*rms_value) ) + self.baseline_radius

            return( radius )


    def read_csv_files(self,csv_file):
        '''
        reads the csv file
        '''
        csv_data = pd.read_csv(csv_file)
        print('CSV file  ' + csv_file +' read succesfully')

        return(csv_data)


    def check_for_micpos():
        '''
        checks if the micpos.csv file is proper or not

        '''

        return()

    def check_for_batpos():
        '''
        '''

        return()

    def check_channels_to_mics(self,mic_pos,mic_audio):
        '''
        checks if the number of mic audio channels and the
        number of xy positions match

        mic_pos: np.array. 1 x (2 x number of mics). with xy positions
        mic_audio: np.array. (N_blocks x num_mics),

        '''
        try:
            num_mics = int(mic_pos.shape[1]/2.0)
        except:
            num_mics = int(mic_pos.shape[0]/2.0)

        num_channels = mic_audio.shape[1]

        if num_mics == num_channels:
            print('number of mics and channels match ')
            return(num_mics,num_channels)
        else:
            raise ValueError('number of mic coordinates and mic channels do not match')

    def gamana_gui(self):
        '''
        simple gui interface which allows user to pick and choose the folder
        and files
        '''
        print('1')
        folder = str(eg.diropenbox('please choose directory where the input files are')) + '\\'
        print('2')


        input_video_path = eg.fileopenbox('please choose the input raw AVI video file',default = folder)

        #extract the original file name from the whole path
        try:
            input_video = os.path.basename(input_video_path)
        except:
            raise Exception('Input file not chosen - please restart and try again')

        filename_prompt = 'Please enter the name of the rms overlayed video file (without .avi at the end) '
        output_video = eg.enterbox(filename_prompt) + '.avi'

        #gui_user_entries =


        #print(output_video)

        self.compile_AV(folder,input_video,output_video)








if __name__ == '__main__':

#    folder = 'C:\\Users\\tbeleyur\\Documents\\gamana_test_data\\barbastelle\\input_hp_folder\\'
#    #'C:\\Users\\tbeleyur\\Documents\\common\\Python_common\\field_viewer\\test_data\\play_av_test\\'
#
#    video = '300717_C1S0043_gamana.avi' #'K3_P09_8000_multibats.avi'
#
#    output_video = 'BARBASTELLE_CAPTURE_ATTEMPT_W_HP_AUDIO.avi'
#    gamana_instance = Gamana()
#    #play_AV(folder+video,output_video,mics_rms,micpos,24)
#    gamana_instance.magnif_factor = 250
#    gamana_instance.baseline_radius = 7
#    gamana_instance.compile_AV(folder,video,output_video,audio_blocksize=150,blocks_per_frame=4,orig_fps=500,DLTdv5=True)

    a = Gamana()
    a.magnif_factor = 350
    a.baseline_radius = 5
    a.gamana_gui()