import i2_temp_contr

value = i2_temp_contr.heat_controler().get_config()
print value

i2_temp_contr.heat_controler().set_tset(65.0)
value = i2_temp_contr.heat_controler().set_ens(1)

value = i2_temp_contr.heat_controler().get_config()
print value

value = i2_temp_contr.heat_controler().get_tact()
print "Actual Temperature now: ", value
