def main(j,jp):
   
    #stop the application (only relevant for server apps)
    
    jp.log("stop $(jp.name)")

    if j.tools.startupmanager.existsJPackage(jp):        
        j.tools.startupmanager.stopJPackage(jp)

    


