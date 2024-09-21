import time
from bms import BMS

def run_test1():
    # Test 1: deep_sleep => run_tests => deep_sleep
    print("Test 1 \n")
    time.sleep(0.5)
    bms1 = BMS()

    print("\nThis will test deep_sleep => run_tests => deep_sleep\n")
    time.sleep(2)

    print("Starting BMS Simulation...\n")

    # Check that we are in deep sleep state
    if (bms1.state != 'deep_sleep'):
        print("Incorrect state: Test failed")
        return

    bms1.button_pressed_5_sec() # Simulate start up, transition to run_tests

    # Check that we are in the run_tests state
    if (bms1.state != 'run_tests'):
        print("Incorrect state: Test failed")
        return

    bms1.diagnostics_pass = False 
    bms1.enter_run_tests() # call enter run tests upon transition
    # assert that state is deep sleep again

    #Check we go back to the deep sleep state
    if (bms1.state != 'deep_sleep'):
        print("Incorrect state: Test failed")
        return
    
    bms1.enter_deep_sleep()
    
    
    #Tests passed, so print test is passed, wait 5 seconds and go onto the next tests
    print("\nTest 1 passed \n")

    time.sleep(2)

def run_test2():
    # Test 2 : deep_sleep => run_tests => idle => normal operation => sleep
    # From normal operation, randomization of parameters
    print("Test 2 \n")
    time.sleep(0.5)
    bms2 = BMS()

    print("\nThis will test transitioning to the normal operation mode and monitoring when the pedal is pressed and not pressed. It will then go to the sleep state\n")
    time.sleep(2)

    print("Starting BMS Simulation...\n")

    bms2.button_pressed_5_sec()  # Simulate start-up, transition to run_tests

    bms2.diagnostics_pass = True  # Simulate diagnostics pass
    bms2.enter_run_tests()  # Transition to idle if diagnostics pass

    # Check that we are in the idle state
    if (bms2.state != 'idle'):
        print("Incorrect state: Test failed")
        return
    
    bms2.enter_idle()
    # wait to simulate time pedal is not pressed
    time.sleep(0.5) # simulate while loop

    bms2.pedal_press = True # Simulate pedal pressed
    print("\nPedal pressed down\n")
    time.sleep(1)
    bms2.enter_idle()

    # Check that we are in normal operation
    if (bms2.state != 'normal_operation'):
        print("Incorrect state: Test failed")
        return
    
    # when the pedal is being pressed in normal operating state
    cycles = 10 # Monitor for 10 cycles before letting go of the pedal
    while bms2.state == 'normal_operation' and cycles != 0:
        bms2.enter_normal_operation()
        time.sleep(0.1)
        # if there is no fault detected, assert that state is still normal operation
        if bms2.fault_check():
            if (bms2.state != 'fault_detected'):
                print("Incorrect state: Test failed")
                return
        # if there is a fault detected, assert that state is now fault operating
        else:
            if (bms2.state != 'normal_operation'):
                print("Incorrect state: Test failed")
                return
        cycles -= 1
    
    time.sleep(1)
    bms2.pedal_press = False
    print("\nTake foot off the pedal\n")

    # When the pedal is not being pressed in normal operating state
    cycles = 10
    while bms2.state == 'normal_operation' and cycles != 0:
        bms2.enter_normal_operation()
        time.sleep(0.1)
        # if there is no fault detected, assert that state is still normal operation
        if bms2.fault_check():
            if (bms2.state != 'fault_detected'):
                print("Incorrect state: Test failed")
                return
        # if there is a fault detected, assert that state is now fault operating
        else:
            if (bms2.state != 'normal_operation'):
                print("Incorrect state: Test failed")
                return
        cycles -= 1

    bms2.button_press = True
    bms2.enter_normal_operation() # Simulate button press (go to sleep)

    if (bms2.state != 'sleep'):
        print("Incorrect state: Test failed")
        return
    
    # Test passed
    print("\nTest 2 passed \n")
    time.sleep(2)

def run_test3():
    # Test 3 : deep_sleep => run_tests => idle => normal operation => fault operating => fatal_fault
    print("Test 3 \n")
    time.sleep(0.5)
    bms3 = BMS()

    print("\nThis will test transitioning to fault operating and fatal fault states when the pedal is pressed indefinitely, causing a fault.\n")
    time.sleep(2)

    print("Starting BMS Simulation...\n")

    bms3.button_pressed_5_sec()  # Simulate start-up, transition to run_tests
    bms3.diagnostics_pass = True  # Simulate diagnostics pass
    bms3.enter_run_tests()  # Transition to idle if diagnostics pass

    # Check that we are in the idle state
    if (bms3.state != 'idle'):
        print("Incorrect state: Test failed")
        return
    
    bms3.enter_idle()
    time.sleep(0.5) # simulate some time in idle

    # Simulate the pedal being pressed down indefinitely
    bms3.pedal_press = True
    print("\nPedal pressed down indefinitely\n")
    time.sleep(1)
    bms3.enter_idle()

    # Check that we are in normal operation
    if (bms3.state != 'normal_operation'):
        print("Incorrect state: Test failed")
        return
    
    # Simulate continuous normal operation with the pedal pressed
    while bms3.state == 'normal_operation':
        bms3.enter_normal_operation()
        time.sleep(0.1)
        
        # Eventually, a fault should occur
        if bms3.fault_check():
            
            # Ensure transition to fault operating state
            if (bms3.state != 'fault_operating'):
                print("Incorrect state: Test failed")
                return
            
            # Simulate fault getting worse over time until fatal fault
            time.sleep(1)
            bms3.enter_fault_operating()
            
            if bms3.fatal_fault_check():
                if (bms3.state != 'deep_sleep'):
                    print("Incorrect state: Test failed")
                    return
            elif (bms3.state != 'fatal_fault'):
                print("Incorrect state: Test failed")
                return
            
            print("\nSystem enncountered fatal fault.\n")
            print(f"Successfully transitioned to {bms3.state}")
            break

    # Test passed
    print("\nTest 3 passed \n")
    time.sleep(2)

def run_test4():
    # Test 4 : deep_sleep => tests => idle => sleep => discharge to storage => deep_sleep
    # Checking discharge to storage by checking soc attribute
    print("Test 4 \n")
    time.sleep(0.5)
    bms4 = BMS()

    print("\nThis test checks that if the button is pressed for 5 seconds, the battery is discharged to 50% SOC before being sent to deep sleep\n")
    time.sleep(2)

    print("Starting BMS Simulation...\n")

    bms4.button_pressed_5_sec()  # Simulate start-up, transition to run_tests

    bms4.diagnostics_pass = True  # Simulate diagnostics pass
    bms4.enter_run_tests()  # Transition to idle if diagnostics pass

    # Check that we are in the idle state
    if (bms4.state != 'idle'):
        print("Incorrect state: Test failed")
        return
    
    bms4.enter_idle()
    # wait to simulate time pedal is not pressed
    time.sleep(0.5) # simulate while loop

    bms4.pedal_press = True # Simulate pedal pressed
    print("\nPedal pressed down\n")
    time.sleep(1)
    bms4.enter_idle()

    # Check that we are in normal operation
    if (bms4.state != 'normal_operation'):
        print("Incorrect state: Test failed")
        return
    
    # when the pedal is being pressed in normal operating state
    cycles = 10 # Monitor for 10 cycles before letting go of the pedal
    while bms4.state == 'normal_operation' and cycles != 0:
        bms4.enter_normal_operation()
        time.sleep(0.1)
        # if there is no fault detected, assert that state is still normal operation
        if bms4.fault_check():
            if (bms4.state != 'fault_detected'):
                print("Incorrect state: Test failed")
                return
        # if there is a fault detected, assert that state is now fault operating
        else:
            if (bms4.state != 'normal_operation'):
                print("Incorrect state: Test failed")
                return
        cycles -= 1
    
    bms4.button_press = True
    bms4.enter_normal_operation() # Simulate button press (go to sleep)

    if (bms4.state != 'sleep'):
        print("Incorrect state: Test failed")
        return
    
    print("\nWe are currently in the sleep state\n")
    time.sleep(1)

    bms4.button_pressed_5_sec() # Simulate 5 second button press

    if (bms4.state != 'discharge_to_storage'): # Check that we are in the discharge to storage state
        print("Incorrect state: Test failed")
        return
    
    bms4.enter_discharge_to_storage() # start draining the battery to 50% SOC

    time.sleep(0.5)

    if (bms4.state != 'deep_sleep'): # Check that we are in the deep sleep after discharging to 50% SOC
        print("Incorrect state: Test failed")
        return
    
    time.sleep(0.2)
    print("\nWe are at 50% SOC and in the deep sleep state for long term storage")
    time.sleep(0.5)
    print("\nTest 4 Passed\n")







def run_test5():
    # Test 5 : deep_sleep => tests => idle => normal => sleep (with depleted SOC) => charging => sleep
    # Checking for charging after use
    print("Test 5 \n")
    time.sleep(0.5)
    bms5 = BMS()

    print("\nThis test checks the charging state and makes sure it refills soc to 100%\n")
    time.sleep(2)

    print("Starting BMS Simulation...\n")

    bms5.button_pressed_5_sec()  # Simulate start-up, transition to run_tests

    bms5.diagnostics_pass = True  # Simulate diagnostics pass
    bms5.enter_run_tests()  # Transition to idle if diagnostics pass

    # Check that we are in the idle state
    if (bms5.state != 'idle'):
        print("Incorrect state: Test failed")
        return
    
    bms5.enter_idle()
    # wait to simulate time pedal is not pressed
    time.sleep(0.5) # simulate while loop

    bms5.pedal_press = True # Simulate pedal pressed
    print("\nPedal pressed down\n")
    time.sleep(1)
    bms5.enter_idle()

    # Check that we are in normal operation
    if (bms5.state != 'normal_operation'):
        print("Incorrect state: Test failed")
        return
    
    # when the pedal is being pressed in normal operating state
    cycles = 10 # Monitor for 10 cycles before letting go of the pedal
    while bms5.state == 'normal_operation' and cycles != 0:
        bms5.enter_normal_operation()
        time.sleep(0.1)
        # if there is no fault detected, assert that state is still normal operation
        if bms5.fault_check():
            if (bms5.state != 'fault_detected'):
                print("Incorrect state: Test failed")
                return
        # if there is a fault detected, assert that state is now fault operating
        else:
            if (bms5.state != 'normal_operation'):
                print("Incorrect state: Test failed")
                return
        cycles -= 1
    
    bms5.button_press = True
    bms5.enter_normal_operation() # Simulate button press (go to sleep)

    if (bms5.state != 'sleep'):
        print("Incorrect state: Test failed")
        return
    
    print("\nWe are currently in the sleep state\n")

    bms5.charger_plugged_in = True # Simulate charger plugged in
    bms5.enter_sleep()

    if (bms5.state != 'charging'): # Check that we are in the charging state
        print("Incorrect state: Test failed")
        return
    
    while (bms5.state == 'charging'):
        bms5.enter_charging()
        time.sleep(1)
    
    if (bms5.state != 'sleep'): # Check that we are in the sleep state after soc is 100
        print("Incorrect state: Test failed")
        return
    
    time.sleep(0.2)
    print("\nWe are fully charged and back in the sleep state")
    time.sleep(0.5)
    print("\nTest 5 Passed\n")
    

