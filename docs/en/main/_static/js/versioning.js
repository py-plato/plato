const initializeVersioning = (config, versions) => {
    const { currentVersion, baseUrl } = config

    const versionList = document.querySelector(".rst-other-versions dl") 
    const versionBanner = document.querySelector(".version-banner")
    
    const versionLink = tag => `${baseUrl}/en/${tag}`
    
    const addVersion = tag => {
        const link = document.createElement("a")
        link.href = versionLink(tag)
        let text = tag
        if (tag === versions.stable) {
            text += " (stable)"
        }
        
        link.appendChild(document.createTextNode(text))

        const dd = document.createElement("dd")
        dd.appendChild(link)

        versionList.appendChild(dd)
    }
    
    versions.dev.forEach(addVersion); 
    versions.released.forEach(addVersion); 
    
    const createLatestLink = () => {
        const link = document.createElement("a")
        link.href = versionLink(versions.stable)
        link.appendChild(document.createTextNode(
            `Go to the latest stable version (${versions.stable}).`
        ))
        return link
    }

    if (!versions.released.includes(`v${currentVersion}`)) {
        versionBanner.classList.add("dev")
        versionBanner.appendChild(document.createTextNode(
            "You are viewing the documentation for the development version. "
        ))
        if (versions.stable) {
            versionBanner.appendChild(createLatestLink())
        }
    } else if (`v${currentVersion}` !== versions.stable) {
        versionBanner.classList.add("outdated")
        versionBanner.appendChild(document.createTextNode(
            "You are viewing the documentation for an old version. "
        ))
        versionBanner.appendChild(createLatestLink())
    }
}

const initializeVersioningFromManifest = (config) => {
    fetch(`${config.baseUrl}/versions.json`).then(response => {
        if (!response.ok) {
            throw new Error("Failed to fetch versions.json manifest")
        }
        return response.json()
    }).then(versions => {
        if (document.readyState === "loading") {
            window.addEventListener("load", () => initializeVersioning(config, versions));
        } else {
            initializeVersioning(config, versions);
        }
    }).catch(error => {
        console.error(error)
    })
}