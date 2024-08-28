# ---------------------------------------------------------------------------- #
#                                                                              #
# 	Module:       main.py                                                      #
# 	Author:       Gavbo                                                        #
# 	Created:      2/14/2024, 11:38:04 AM                                       #
# 	Description:  V5 project                                                   #
#                                                                              #
# ---------------------------------------------------------------------------- #


from vex import *
import math
# Brain should be defined by default
brain=Brain()

brain.screen.print("starting up!")


"""Intializing Robot"""
#states
IDLE = 0
TURNING = 1
NAVIGATING = 2
SEARCHING = 3
LOCATING = 4
POSITIONING = 5
DROPPING = 6
REPOSITIONING = 7
RETURNING = 8
DELIVERING = 9
EMPTYING = 10
RESTORING = 11
FIXING = 12
MOVING = 13

"""Color Codes for identifing Robot"""
GRAPEFRUIT = Signature(1, 5553, 5871, 5712, 893, 1251, 1072, 3.000, 0)
ORANGE_FRUIT = Signature(2, 6625, 7955, 7290, -2209, -1923, -2066, 3.000, 0)
LIME  = Signature(3, -5135, -3831, -4483, -3659, -3099, -3379, 3.000, 0)
LEMON = Signature(4, 2669, 2971, 2820, -3599, -3365, -3482, 3.000, 0)
camera = Vision(Ports.PORT6, 43, GRAPEFRUIT, ORANGE_FRUIT, LIME, LEMON)

"""intializing timer"""
t1 = Timer()

"""Basket Color Codes"""
ORANGE_BASKET = Code(ORANGE_FRUIT, GRAPEFRUIT)
LEMON_BASKET = Code(LEMON, GRAPEFRUIT)
LIME_BASKET = Code(LIME, GRAPEFRUIT)
camera2 = Vision(Ports.PORT7, 43, GRAPEFRUIT,ORANGE_FRUIT ,LIME,LEMON)

#setting the motors 
left_motor = Motor(Ports.PORT2, GearSetting.RATIO_18_1,True)
right_motor = Motor(Ports.PORT1, GearSetting.RATIO_18_1,False)
arm_motor = Motor(Ports.PORT3, GearSetting.RATIO_36_1)
basket_motor = Motor(Ports.PORT4, GearSetting.RATIO_18_1)
buttonD = Bumper(brain.three_wire_port.e)
imu = Inertial(Ports.PORT5)

sonar_right = Sonar(brain.three_wire_port.g)
sonar_left = Sonar(brain.three_wire_port.a)
sonar_front = Sonar(brain.three_wire_port.c)

"""Gains and Speeds"""
#gains
arm_gain = 0.2
side_gain_derivative = 0.25
side_gain_proportional = 1.8

#speed
speed_turn = 120
arm_speed = 30
basket_speed = 50


"""IDLE STATE"""
#check for button presses
prevButton = False 
buttonCount = 0
def checkForButtonPress():
    global prevButton
    retVal = False
    currButton = buttonD.pressing()
    if((not currButton) and prevButton):
        retVal = True
    prevButton = currButton
    return retVal

def handleButton():
    global state
    global buttonCount
    buttonCount += 1
    print(buttonCount)

    if(state == IDLE):
        print("IDLE -> NAVIGATING")
        imu.calibrate()
        while imu.is_calibrating(): wait(100)
        imu.set_heading(0)
        state = NAVIGATING

    elif(state != IDLE):
        print("State -> IDLE")
        state = IDLE
        left_motor.stop()
        right_motor.stop()


"""TURNING STATE"""

#translation of the angle to negative degrees    
def translate_angle(angle):
     if (angle > 180):
         return angle - 360
     return angle 

#turn funciton using IMU heading
def better_handleTurn(degrees_to_turn):
    global state
    kturn = 5
    retval = False
    current_heading = translate_angle(imu.heading())
    # print("heading is ",current_heading)
    error = degrees_to_turn - current_heading
    # print("error is ",error)
    if error < -180:
        error += 180
    if abs(error) > 3:
        effort = error * kturn
        if (error > 0):
            right_motor.spin(FORWARD, effort, RPM)
            left_motor.spin(FORWARD, - effort, RPM)
        elif (error < 0):
            right_motor.spin(FORWARD,- effort,RPM)
            left_motor.spin(FORWARD, effort, RPM)
    else:
        right_motor.stop()
        left_motor.stop()
        retval = True
    return retval

"""NAVAGATING STATE"""
#wall following function
def wall_follow(target_distance, normal_speed,side):
    global previous_side_sonar_value
    if side == 1: 
        sonar_side_distance = sonar_right.distance(MM)
        if(sonar_side_distance > 300):
            sonar_side_distance = previous_side_sonar_value
        error_side = sonar_side_distance - target_distance
        effort = (side_gain_proportional * error_side)+ ((side_gain_derivative) * (sonar_side_distance - previous_side_sonar_value))
        previous_side_sonar_value = error_side
        right_motor.spin(FORWARD, (normal_speed - effort))
        left_motor.spin(FORWARD, (normal_speed + effort))
    if side == 2:
        sonar_side_distance = sonar_left.distance(MM)
        if(sonar_side_distance > 300):
            sonar_side_distance = previous_side_sonar_value
        # print(sonar_side_distance)
        error_side = sonar_side_distance - target_distance
        effort = (side_gain_proportional * error_side)+ ((side_gain_derivative) * (sonar_side_distance - previous_side_sonar_value))
        previous_side_sonar_value = error_side
        right_motor.spin(FORWARD, (normal_speed + effort))
        left_motor.spin(FORWARD, (normal_speed - effort))
    

#check for fruit on trees to the left of it. 
current_index = 0
def is_fruit_on_left(tree_index):
    global state
    global next_state
    global current_index  
    if(current_index == 3):
        state = IDLE
        left_motor.stop()
        right_motor.stop()
        print("bob is happy")
    elif(sonar_left.distance(MM) < 350 and current_index != tree_index):
        wait(3000) #could use a timer to be more reliable for future additions
        current_index += 1
    elif(sonar_left.distance(MM) < 350 and current_index == tree_index):
        global angle
        if fruit_in_basket == 0:
            left_motor.spin_for(REVERSE, 1000, DEGREES, 100, RPM, False)
            right_motor.spin_for(REVERSE, 1000, DEGREES, 100, RPM) 
            state = TURNING
            angle = -70
            next_state = SEARCHING 
        else:
            t3.reset()
            state = MOVING #error in code here
            print("dead reckoning!")
        
        


"""SEARCHING STATE""" 
#Finds closest fruit and identifies its color:
def update_fruit(fruit):
    #this is a helper function for "arm_for_fruit" function
    global current_fruit
    global state
    global fruit_basket
    if(camera.take_snapshot(fruit)  and camera.largest_object().height > 25): 
            print('Found a fruit!')
            current_fruit = fruit
            if(fruit == LIME):
                fruit_basket = LIME_BASKET
            if(fruit == LEMON):
                fruit_basket = LEMON_BASKET
            if(fruit == ORANGE_FRUIT):
                fruit_basket = ORANGE_BASKET

            
def arm_for_fruit():
    global state
    if(current_fruit == None):
        update_fruit(GRAPEFRUIT)
        update_fruit(LEMON)
        update_fruit(ORANGE_FRUIT)
        update_fruit(LIME)
        if arm_motor.position() < 300:
            arm_motor.spin(FORWARD, 10, RPM)
        else:
            wait(100)
            arm_motor.stop()
            print("fail") 
    else:
        arm_motor.stop()
        state = POSITIONING
        print("searching --> positioning")


"""POSITIONING STATE"""
#puts the arm in the position to pick the fruit 
#use with a if statement to go to the dropping state 
def position(fruit, center_hieght):
    global state
    retval = False
    retval2 = False
    k = 0.4
    fruit_presented = camera.take_snapshot(fruit)
    if fruit_presented:
        y_center = camera.largest_object().centerY
        error = center_hieght - y_center
        effort = arm_gain * error
        if abs(error) < 7:
            arm_motor.stop()
            retval = True
        else:
            arm_motor.spin(FORWARD,effort)
        #centering code
        x_center = (150)
        cx = camera.largest_object().centerX
        error2 = cx - x_center
        effort2 = error2 * k
        if(abs(error) < 7):
            left_motor.stop()
            right_motor.stop()
            retval2 = True 
        else:
            left_motor.spin(FORWARD, effort2)
            right_motor.spin(FORWARD, - effort2)
    if retval and retval2:
        return True
    
    else:
        return False


"""LOCATING STATE"""
#better version of the approach
"""IF the robot has been in this state for 7 seconds switch back to positioning"""
def approach_fruit(fruit):
    global state
    kp1 = 0.7
    height_of_camera = 175
    objects2 = camera.take_snapshot(fruit)
    timer_value = t1.value()    
    if(objects2):
        height_measured = camera.largest_object().height
        error = (height_measured - height_of_camera)
        # print(height_measured)
        effort = error * kp1
        right_motor.spin(FORWARD, -effort, RPM)
        left_motor.spin(FORWARD, -effort, RPM)
        if (abs(error) < 8):
            right_motor.stop()
            left_motor.stop()
            if (True):
                state = FIXING
                print("locating ---> Fixing")
        elif(error > 190):
            left_motor.spin_for(REVERSE, 720, DEGREES, 30, RPM, False)
            right_motor.spin_for(REVERSE, 720, DEGREES, 30, RPM)
            


"""DROPPING STATE""" 
#target height is 90 right now
prev_error_drop = 0
def drop(fruit, target_height=210):
    kp = 0.2
    global prev_error_drop 
    global state
    global fruit_in_basket
    global next_state
    global angle
    global flag1
    objects = camera.take_snapshot(fruit)
    if (objects):
        height = camera.largest_object().height
        error = target_height - height
        effort = error*kp
        if(error < 12):
            left_motor.spin_for(FORWARD,300,DEGREES, False)
            right_motor.spin_for(FORWARD,300,DEGREES)
            arm_motor.spin_for(REVERSE, 0.4, TURNS)
            fruit_in_basket += 1
            print("collected")
            print("dropping --> repositioning")
            next_state = REPOSITIONING
            state = TURNING
            angle = 90
            # left_motor.spin_for(REVERSE, 720, DEGREES, 30, RPM, False)
            # right_motor.spin_for(REVERSE, 720, DEGREES, 30, RPM)
        elif(error > 100 and flag1):
            left_motor.spin_for(REVERSE, 720, DEGREES, 30, RPM, False)
            right_motor.spin_for(REVERSE, 720, DEGREES, 30, RPM)
            flag1 = False
        else:
            left_motor.spin(FORWARD, effort, RPM)
            right_motor.spin(FORWARD, effort, RPM)
        prev_error_drop = error

"""Repositioning state"""
#used to reset the robot after targeting a fruit. 
def reposition():
    global state
    global next_state
    global angle
    global repo_value
    front_value = sonar_front.distance(MM)
    if(front_value < 100):
        if(fruit_in_basket > 1):
            next_state = RETURNING
            state = TURNING
            angle = 180
            repo_value = True
        else:
            #rewrite so that it quickly reverses and turns until it finds the next fruit
            next_state = NAVIGATING
            state = TURNING
            angle = 0
            repo_value = True
    else:
        right_motor.spin(FORWARD, 150, RPM)
        left_motor.spin(FORWARD, 150, RPM)


"""RETURNING STATE"""
def start_returning():
    global state
    global angle
    global next_state
    front_sonar_value = sonar_front.distance(MM)
    if(front_sonar_value < 100 and front_sonar_value != 0):
        right_motor.stop()
        left_motor.stop()
        state = EMPTYING
        print("return to empty")
    else: 
        wall_follow(200,160,2)


"""DELIVERY STATE"""
#matts code goes here
def deliver(inbetween_distance):
    global state
    global next_state
    global angle
    if  current_fruit != None:
        state = EMPTYING
        print("delivery to emptying")
    # elif current_fruit == LEMON:
    #     next_state = EMPTYING
    #     go_inches_straight(inbetween_distance, 150, -90)
    #     state = TURNING
    #     angle = 179
    #     print("delivery to emptying")
    # elif current_fruit == ORANGE_FRUIT:
    #     next_state = EMPTYING 
    #     go_inches_straight(inbetween_distance*2, 150, -90)
    #     state = TURNING
    #     angle = 179
    #     print("delivery to emptying")
"""EMPTYING STATE"""
def empty():
    global state
    global angle
    global next_state
    right_motor.spin_for(FORWARD, 200, DEGREES, False)
    left_motor.spin_for(FORWARD, 200, DEGREES)
    arm_motor.spin_to_position(100)
    basket_motor.spin_to_position(-310,DEGREES,20, RPM)
    sleep(2000)
    basket_motor.spin_to_position(300,DEGREES,20, RPM)
    right_motor.spin_for(REVERSE, 1000, DEGREES, False)
    left_motor.spin_for(REVERSE, 1000, DEGREES)
    next_state = RESTORING
    state = TURNING
    angle = 90
    print("empty --> restoring")

"""RESTORING STATE"""
# poopy state for getting back to the best spot ever to get maxium fruit! 
def restore():
    global next_state
    global state
    global angle
    global current_fruit
    global fruit_basket
    global number_of_trees_collected
    global fruit_in_basket
    global current_index
    distance = sonar_front.distance(MM)
    if distance < 150:
        next_state = NAVIGATING
        state = TURNING
        angle = 0
        current_fruit = None
        fruit_basket = None
        number_of_trees_collected += 1
        current_index = 0
        fruit_in_basket = 0
    else: 
        right_motor.spin(FORWARD, 150, RPM)
        left_motor.spin(FORWARD, 150, RPM)
    
"""FIXING STATE"""
def fix(center_height, fruit):
    global state
    retval = False
    retval2 = False
    k = 0.4
    k2 = 0.4
    fruit_presented = camera.take_snapshot(fruit)
    if fruit_presented:
        y_center = camera.largest_object().centerY
        error = center_height - y_center
        effort = k2 * error
        if abs(error) < 7:
            arm_motor.stop()
            retval = True
        else:
            arm_motor.spin(FORWARD,effort)
        #centering code
        x_center = (150)
        cx = camera.largest_object().centerX
        error2 = cx - x_center
        effort2 = error2 * k
        if(abs(error) < 7):
            left_motor.stop()
            right_motor.stop()
            retval2 = True 
        else:
            left_motor.spin(FORWARD, effort2)
            right_motor.spin(FORWARD, - effort2)
    if retval and retval2:
        return True
    
    else:
        return False

"""moving state!!!!"""
def move():
    global state
    global angle
    global next_state
    time1 =t3.value()
    if time1 > 4:
        state = TURNING
        angle = -110 
        next_state = SEARCHING
        print("moving ---> TURNING")
    else:
        wall_follow(180,150,1)


"""WHILE LOOP FOR ROBOT"""
# looop code for the main while loop
current_fruit = None
fruit_basket = None
state = IDLE
previous_side_sonar_value = 0
previous_state = None
angle = None
fruit_in_basket = 0
number_of_trees_collected = 0
print(camera.installed())
basket_motor.reset_position()
arm_motor.reset_position()
flag1 = True
repo_value = True
intial_heading = 0
t3 = Timer()

while True:
    if checkForButtonPress(): 
        handleButton()
        t = Timer()
    #idle ---> navigating / any ----> idle 
    if(state == NAVIGATING): wall_follow(160,130,1)
    #if(state == NAVIGATING): is_wall_ahead(50)
    if(state == NAVIGATING): is_fruit_on_left(number_of_trees_collected)
    # #nav --> turning
    if(state == TURNING): 
        # turning_new(90,intial_heading)
        if (better_handleTurn(angle)):
            state = next_state
            next_state = None
    # #nav ---> searching
    if(state == SEARCHING): arm_for_fruit()
    # #seaching --> positioning
    if(state == POSITIONING):
        if (position(current_fruit,145)):
            state = LOCATING
            print("positioning to locating")
            t1 = Timer()
    # positioning ---> locating
    if(state == LOCATING): 
        approach_fruit(current_fruit)
    # #positioning ---> Dropping
    if(state == DROPPING):
        drop(current_fruit)
    # Dropping ---> REPO
    if(state == REPOSITIONING):
        reposition()
    #Repositioning ---> returning
    if (state == RETURNING): start_returning()
    #returning ---> delivery
    if(state == DELIVERING):
        deliver(15) 
    #deliver --- > emptying
    if(state == EMPTYING):
        empty()
    if state == RESTORING:
        restore()
    if state == FIXING:
        if(fix(150, current_fruit)):
            state = DROPPING
            print("fixing --> dropping")
    if state == MOVING:
        move()