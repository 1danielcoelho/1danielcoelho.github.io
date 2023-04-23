from pathlib import Path
import binascii

bytes_to_read = 2000
guids = {
    "Dev-Blueprints": "B0D832E41F894F0DACCF7EB736FD4AA2",
    "Dev-Build": "E1C64328A22C4D53A36C8E866417BD8C",
    "Dev-Core": "375EC13C06E448FBB50084F0262A717E",
    "Dev-Editor": "E4B068EDF49442E9A231DA0B2E46BB41",
    "Dev-Framework": "CFFC743F43B04480939114DF171D2073",
    "Dev-Mobile": "B02B49B5BB2044E9A30432B752E40360",
    "Dev-Networking": "A4E4105C59A149B5A7C540C4547EDFEE",
    "Dev-Online": "39C831C95AE647DC9A449C173E1C8E7C",
    "Dev-Physics": "78F01B33EBEA4F98B9B484EACCB95AA2",
    "Dev-Platform": "6631380F2D4D43E08009CF276956A95A",
    "Dev-Rendering": "12F88B9F88754AFCA67CD90C383ABD29",
    "Dev-Sequencer": "7B5AE74CD2704C10A95857980B212A5A",
    "Dev-VR": "D72969181DD64BDD9DE264A83CC13884",
    "Dev-LoadTimes": "C2A15278BFE74AFE6C1790FF531DF755",
    "Private-Geometry": "6EACA3D440EC4CC1b7868BED09428FC5",
    "Dev-AnimPhys": "29E575DDE0A346279D10D276232CDCEA",
    "Dev-Anim": "AF43A65D7FD3494798733E8ED9C1BB05",
    "Dev-ReflectionCapture": "6B266CEC1EC74B8FA30BE4D90942FC07",
    "Dev-Automation": "0DF73D61A23F47EAB72789E90C41499A",
    "FortniteMain": "601D1886AC644F84AA16D3DE0DEAC7D6",
    "FortniteRelease": "E70863686B234C5884391B7016265E91",
    "Dev-Enterprise": "9DFFBCD6494F0158E22112823C92A888",
    "Dev-Niagara": "F2AED0AC9AFE416F8664AA7FFA26D6FC",
    "Dev-Destruction": "174F1F0BB4C645A5B13F2EE8D0FB917D",
    "Dev-Physics-Ext": "35F94A83E258406CA31809F59610247C",
    "Dev-PhysicsMaterial-Chaos": "B68FC16E8B1B42E2B453215C058844FE",
    "Dev-CineCamera": "B2E185064273CFC2A54EF4BB758BBA07",
    "Dev-VirtualProduction": "64F58936FD1B42BABA967289D5D0FA4E",
    "Dev-MediaFramework": "6f0ed827a60948959c91998d90180ea4",
    "Release": "9C54D522A8264FBE9421074661B482D0",
}
# Leave these at -1 to just read the asset values. Put some other value here to downgrade the custom version to it
updated_values = {
    "Dev-Rendering": 44,  
    "Dev-Physics-Ext": 40,
    "FortniteMain": 43,
    "Release": 38,
}
target_folder = r"E:\Work\Unreal projects\Retail4262\Content\From427"
asset_types = ["uasset", "umap"]

update_engine_version = True
engine_major_version = 4
engine_minor_version = 26
engine_changelist = 15973114
asset_major_version = 4
asset_minor_version = 27
asset_changelist = 16724560

def collect_files(folder_root, formats):
    result = []
    for fmt in formats:
        for path in Path(folder_root).rglob('*.' + fmt):
            result.append(str(path))
    return result

def build_version_bytes(major, minor, changelist):
    result = bytearray()
    result += major.to_bytes(2, byteorder="little")  # Major version stored in a short
    result += minor.to_bytes(4, byteorder="little")  # Minor version stored in an int
    result += changelist.to_bytes(4, byteorder="little")  # CL stored in an int
    return result

def flip_endianess(orig_bytes):
    result = bytearray([0]*16)
    
    index = 0
    for chunk in range(4):
        for byte_index in [3, 2, 1, 0]:
            result[index] = orig_bytes[chunk * 4 + byte_index]
            index += 1

    return result

guids_bytes = {key:flip_endianess(binascii.unhexlify(value)) for (key, value) in guids.items()}
asset_version_bytes = build_version_bytes(asset_major_version, asset_minor_version, asset_changelist)
engine_version_bytes = build_version_bytes(engine_major_version, engine_minor_version, engine_changelist)
assert(len(asset_version_bytes) == len(engine_version_bytes))

for file_path in collect_files(target_folder, asset_types):
    print(file_path)
    with open(file_path, "r+b") as f:
        chunk = f.read(bytes_to_read)

        print(f"File: '{file_path}'")

        # Update custom versions
        for (entry, new_value) in updated_values.items():
            guid = guids_bytes[entry]
            
            index = chunk.find(guid)
            if index == -1:
                print(f"\tCouldn't find custom version '{entry}'")
                continue

            value_index = index + len(guid)
            asset_value = int.from_bytes(chunk[value_index:value_index+4], byteorder="little")

            if new_value != -1:
                if new_value >= asset_value:
                    print(f"\tLeft '{entry}' at '{chunk[value_index]}'")      
                    continue  
                
                f.seek(value_index)
                f.write(new_value.to_bytes(4, byteorder="little"))

                print(f"\tDowngraded '{entry}' from '{asset_value}' to '{new_value}'")        
            else:
                print(f"\tRead '{entry}' with value '{asset_value}'")        

        # Update engine version (we do this twice because we could have engine and "compatible" changelist)
        if update_engine_version:
            index = chunk.find(asset_version_bytes)
            if index != -1:
                print(f"\tReplaced first occurence of asset version '{binascii.hexlify(asset_version_bytes)}' with '{binascii.hexlify(engine_version_bytes)}'")
                f.seek(index)
                f.write(engine_version_bytes)

            index = chunk.find(asset_version_bytes, index+1)
            if index != -1:
                print(f"\tReplaced second occurence of engine version '{binascii.hexlify(asset_version_bytes)}' with '{binascii.hexlify(engine_version_bytes)}'")
                f.seek(index)
                f.write(engine_version_bytes)
    print("")
