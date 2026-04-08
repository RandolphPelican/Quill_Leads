# Mock inventory for rare/old computer parts

MOCK_INVENTORY = [
    {
        "id": "cpu_8086",
        "part_number": "D8086",
        "name": "Intel 8086 CPU",
        "description": "16-bit CPU from 1978, used in early IBM PCs.",
        "specs": "Clock: 5MHz, Bus: 16-bit",
        "category": "processor"
    },
    {
        "id": "cpu_8088",
        "part_number": "D8088",
        "name": "Intel 8088 CPU",
        "description": "8-bit bus version of 8086, used in original IBM PC.",
        "specs": "Clock: 4.77MHz, Bus: 8-bit",
        "category": "processor"
    },
    {
        "id": "cpu_80286",
        "part_number": "D80286",
        "name": "Intel 80286 CPU",
        "description": "16-bit CPU with protected mode, used in IBM PC AT.",
        "specs": "Clock: 6-12MHz, Bus: 16-bit",
        "category": "processor"
    },
    {
        "id": "cpu_80386",
        "part_number": "D80386",
        "name": "Intel 80386 CPU",
        "description": "32-bit CPU, first x86 with 32-bit architecture.",
        "specs": "Clock: 16-33MHz, Bus: 32-bit",
        "category": "processor"
    },
    {
        "id": "cpu_80486",
        "part_number": "D80486",
        "name": "Intel 80486 CPU",
        "description": "32-bit CPU with built-in math coprocessor.",
        "specs": "Clock: 25-50MHz, Bus: 32-bit",
        "category": "processor"
    },
    {
        "id": "ram_30pin",
        "part_number": "SIMM-30-1MB",
        "name": "1MB 30-pin SIMM",
        "description": "30-pin SIMM memory module, 1MB capacity.",
        "specs": "Capacity: 1MB, Type: FPM, Pins: 30",
        "category": "memory"
    },
    {
        "id": "ram_30pin_4mb",
        "part_number": "SIMM-30-4MB",
        "name": "4MB 30-pin SIMM",
        "description": "30-pin SIMM memory module, 4MB capacity.",
        "specs": "Capacity: 4MB, Type: FPM, Pins: 30",
        "category": "memory"
    },
    {
        "id": "ram_72pin",
        "part_number": "SIMM-72-8MB",
        "name": "8MB 72-pin SIMM",
        "description": "72-pin SIMM memory module, 8MB capacity.",
        "specs": "Capacity: 8MB, Type: FPM, Pins: 72",
        "category": "memory"
    },
    {
        "id": "hdd_mfm",
        "part_number": "ST225",
        "name": "Seagate ST225 MFM Hard Drive",
        "description": "5.25-inch MFM hard drive, 20MB capacity.",
        "specs": "Capacity: 20MB, Interface: MFM, Form Factor: 5.25-inch",
        "category": "storage"
    },
    {
        "id": "hdd_ide",
        "part_number": "WDAC2400",
        "name": "Western Digital Caviar 400MB",
        "description": "3.5-inch IDE hard drive, 400MB capacity.",
        "specs": "Capacity: 400MB, Interface: IDE, Form Factor: 3.5-inch",
        "category": "storage"
    },
    {
        "id": "fdd_525",
        "part_number": "TEAC-FD55",
        "name": "5.25-inch Floppy Drive",
        "description": "5.25-inch floppy disk drive, 1.2MB capacity.",
        "specs": "Capacity: 1.2MB, Interface: 34-pin, Form Factor: 5.25-inch",
        "category": "storage"
    },
    {
        "id": "fdd_35",
        "part_number": "TEAC-FD235",
        "name": "3.5-inch Floppy Drive",
        "description": "3.5-inch floppy disk drive, 1.44MB capacity.",
        "specs": "Capacity: 1.44MB, Interface: 34-pin, Form Factor: 3.5-inch",
        "category": "storage"
    },
    {
        "id": "gpu_vga",
        "part_number": "TSENG-ET4000",
        "name": "Tseng Labs ET4000 VGA Card",
        "description": "ISA VGA graphics card with 512KB memory.",
        "specs": "Memory: 512KB, Interface: ISA, Resolution: 640x480",
        "category": "graphics"
    },
    {
        "id": "gpu_isa",
        "part_number": "ATI-VGAWONDER",
        "name": "ATI VGA Wonder",
        "description": "ISA VGA graphics card, 256KB memory.",
        "specs": "Memory: 256KB, Interface: ISA, Resolution: 640x480",
        "category": "graphics"
    },
    {
        "id": "sound_sb",
        "part_number": "CT1350B",
        "name": "Creative Sound Blaster 2.0",
        "description": "8-bit ISA sound card with FM synthesis.",
        "specs": "Interface: ISA, Channels: Stereo, DAC: 8-bit",
        "category": "sound"
    },
    {
        "id": "modem_14400",
        "part_number": "USR-14400",
        "name": "US Robotics Sportster 14.4",
        "description": "14.4kbps external modem with serial interface.",
        "specs": "Speed: 14.4kbps, Interface: Serial, Type: External",
        "category": "communication"
    },
    {
        "id": "modem_28800",
        "part_number": "USR-28800",
        "name": "US Robotics Sportster 28.8",
        "description": "28.8kbps external modem with serial interface.",
        "specs": "Speed: 28.8kbps, Interface: Serial, Type: External",
        "category": "communication"
    },
    {
        "id": "nic_isa",
        "part_number": "3C509-TP",
        "name": "3Com EtherLink III",
        "description": "ISA Ethernet card with RJ-45 connector.",
        "specs": "Interface: ISA, Speed: 10Mbps, Connector: RJ-45",
        "category": "networking"
    },
    {
        "id": "psu_at",
        "part_number": "AT-200W",
        "name": "AT Power Supply 200W",
        "description": "AT form factor power supply, 200W output.",
        "specs": "Form Factor: AT, Wattage: 200W, Connectors: AT",
        "category": "power"
    },
    {
        "id": "case_at",
        "part_number": "AT-TOWER",
        "name": "AT Tower Case",
        "description": "Full tower AT case with 5.25-inch bays.",
        "specs": "Form Factor: AT, Bays: 5x 5.25-inch, 3x 3.5-inch",
        "category": "case"
    }
]