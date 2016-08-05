package com.example.ayush.droneflashing;

import android.content.Context;
import android.hardware.Camera;
import android.hardware.camera2.CameraAccessException;
import android.hardware.camera2.CameraManager;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.view.View;
import android.widget.*;

import java.util.ArrayList;
import java.util.Timer;
import java.util.TimerTask;


public class MainActivity extends AppCompatActivity {

    //rate of each bit in milliseconds
    private final int TIC_RATE = 200;

    //list containing all the fields
    ArrayList<EditText> fields = new ArrayList<EditText>();


    //flash related variables
    private boolean isFlashOn;
    private CameraManager manager;
    private Camera cam;
    private Timer timer;



    @Override
    protected void onCreate(Bundle savedInstanceState) {

        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        Button btnStart = (Button)findViewById(R.id.ButtonStart);
        Button btnReset = (Button)findViewById(R.id.ButtonReset);

        //access all the fields
        fields.add((EditText)findViewById(R.id.Field1));
        fields.add((EditText)findViewById(R.id.Field2));
        fields.add((EditText)findViewById(R.id.Field3));
        fields.add((EditText)findViewById(R.id.Field4));
        fields.add((EditText)findViewById(R.id.Field5));
        fields.add((EditText)findViewById(R.id.Field6));
        fields.add((EditText)findViewById(R.id.Field7));
        fields.add((EditText)findViewById(R.id.Field8));

        //temporary hardcoding for pattern
        fields.get(0).setText("1");
        fields.get(1).setText("0");
        fields.get(2).setText("1");
        fields.get(3).setText("0");
        fields.get(4).setText("1");
        fields.get(5).setText("1");
        fields.get(6).setText("1");
        fields.get(7).setText("0");

        //setting up Camera
        manager = (CameraManager) getSystemService(Context.CAMERA_SERVICE);
        isFlashOn = false;

        //reset button listener
        if (btnReset != null) {
            btnReset.setOnClickListener(new View.OnClickListener() {

                @Override
                public void onClick(View v) {

                    //turn off timer
                    if(timer != null) {
                        timer.cancel();
                        timer.purge();
                    }

                    turnFlashOff();

                    //reset all field values;
                    for(EditText field: fields)
                        field.setText("0");

                }
            });
        }

        //start button listener
        if (btnStart != null) {
            btnStart.setOnClickListener(new View.OnClickListener() {

                @Override
                public void onClick(View v) {


                    //reset timer
                    if(timer != null) {
                        timer.cancel();
                        timer.purge();
                    }

                    timer = new Timer();
                    timer.scheduleAtFixedRate(new TimerTask() {

                        int count = 0;


                        @Override
                        public void run() {

                            //check whether each field is equal to zero
                            if(fields.get(count).getText().toString().equals("0"))
                                turnFlashOff();
                            else
                                turnFlashOn();

                            //iterate through each of the fields
                            count++;

                            //reset current iteration whenever necessary
                            if(count >= fields.size())
                                count = 0;

                        }
                    }, 0, TIC_RATE);
                }
            });
        }
    }

    //TODO: Figure out what is causing Error 1001.(Probably something related to the old Camera API)

    private void turnFlashOn(){

        if(!isFlashOn) {

            //if user is on marshmallow, use latest torch api
            if (android.os.Build.VERSION.SDK_INT >= 23) {
                try {
                    manager.setTorchMode(manager.getCameraIdList()[0], true);
                } catch (CameraAccessException e) {
                    e.printStackTrace();
                }
            } else {
                if(cam == null)
                    cam = Camera.open();
                Camera.Parameters p = cam.getParameters();
                p.setFlashMode(Camera.Parameters.FLASH_MODE_TORCH);
                cam.setParameters(p);
                cam.startPreview();
            }
        }

        isFlashOn = true;
    }

    private void turnFlashOff(){

        if(isFlashOn) {

            //if user is on marshmallow, use latest torch api
            if (android.os.Build.VERSION.SDK_INT >= 23) {
                try {
                    manager.setTorchMode(manager.getCameraIdList()[0], false);
                    isFlashOn = false;
                } catch (CameraAccessException e) {
                    e.printStackTrace();
                }
            } else {
                if(cam == null)
                    cam = Camera.open();
                Camera.Parameters p = cam.getParameters();
                p.setFlashMode(Camera.Parameters.FLASH_MODE_OFF);
                cam.setParameters(p);
                cam.stopPreview();
            }
        }
        isFlashOn = false;
    }
}
